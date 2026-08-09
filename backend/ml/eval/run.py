"""Run the intake extraction eval against any OpenAI-compatible endpoint.

    cd backend
    python -m ml.eval.run --label "7b-router" --model "Qwen/Qwen2.5-7B-Instruct"
    python -m ml.eval.run --label "0.5b-q4" --base-url http://localhost:8080/v1 \
        --api-key local --model qwen2.5-0.5b-instruct-q4_k_m

Prompts come from ``build_intake_messages`` and the decode settings come from
``INTAKE_PARSE_*``, both in ``app.llm.intake.service``, so this cannot score a request
production never sends. The reply is read raw: no fence-stripping, no retry, because
raw JSON validity is one of the numbers being measured.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

from openai import APIStatusError, AsyncOpenAI, OpenAIError

from app.core.config import settings
from app.llm.intake.service import (
    INTAKE_PARSE_MAX_TOKENS,
    INTAKE_PARSE_TEMPERATURE,
    build_intake_messages,
)
from app.llm.providers.huggingface import structured_output_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput
from ml.eval.metrics import (
    TurnScore,
    aggregate,
    by_category,
    fmt,
    markdown_row,
    parse_raw_output,
    score_turn,
)
from ml.paths import EVAL_DATASET_PATH, QUESTIONS_PATH, RESULTS_DIR

# Aborting the whole run on these avoids burning an entire dataset against a dead key.
FATAL_STATUS = {401, 402, 403}


class FatalRunError(RuntimeError):
    """An account-level failure: every remaining turn would fail the same way."""


def load_questions(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dataset(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_number} is not valid JSON: {exc}") from exc
    return rows


async def run_turn(
    client: AsyncOpenAI,
    turn: dict[str, Any],
    *,
    questions: list[dict[str, Any]],
    model: str,
    duplicate_schema: bool,
    json_mode: bool,
    score_next_question: bool,
) -> tuple[TurnScore, str]:
    """Send one turn and score the raw reply. Returns (score, raw text)."""
    prompt = build_intake_messages(
        user_input=turn["user_input"],
        current_criteria=turn.get("current_criteria") or {},
        questions=questions,
    )
    messages = prompt.messages
    if duplicate_schema:
        # Pre-P1 behaviour: the provider prepended a second schema copy. Intake now
        # passes include_schema_instruction=False, so this is off by default.
        messages = structured_output_messages(
            messages=messages,
            response_format=LlmParseModelOutput,
        )

    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": INTAKE_PARSE_TEMPERATURE,
        "max_tokens": INTAKE_PARSE_MAX_TOKENS,
    }
    if json_mode:
        request["response_format"] = {"type": "json_object"}

    started = time.perf_counter()
    try:
        completion = await client.chat.completions.create(**request)
    except APIStatusError as exc:
        if exc.status_code in FATAL_STATUS:
            raise FatalRunError(f"{exc.status_code} from the endpoint: {exc}") from exc
        return _error_score(turn, prompt, started, str(exc), score_next_question), ""
    except OpenAIError as exc:
        return _error_score(turn, prompt, started, str(exc), score_next_question), ""

    latency_ms = (time.perf_counter() - started) * 1000
    raw_text = (completion.choices[0].message.content or "").strip()
    raw_valid, schema_valid, parsed = parse_raw_output(raw_text)
    usage = completion.usage

    score = score_turn(
        turn_id=turn["id"],
        category=turn.get("category", "uncategorized"),
        gold=turn["gold"],
        predicted=parsed,
        required_fields=prompt.required_fields,
        question_keys=prompt.question_keys,
        raw_json_valid=raw_valid,
        schema_valid=schema_valid,
        latency_ms=latency_ms,
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        score_next_question=score_next_question,
    )
    return score, raw_text


def _error_score(
    turn: dict[str, Any],
    prompt: Any,
    started: float,
    message: str,
    score_next_question: bool,
) -> TurnScore:
    return score_turn(
        turn_id=turn["id"],
        category=turn.get("category", "uncategorized"),
        gold=turn["gold"],
        predicted=None,
        required_fields=prompt.required_fields,
        question_keys=prompt.question_keys,
        raw_json_valid=False,
        schema_valid=False,
        latency_ms=(time.perf_counter() - started) * 1000,
        score_next_question=score_next_question,
        error=message,
    )


async def run_dataset(
    turns: list[dict[str, Any]],
    *,
    client: AsyncOpenAI,
    questions: list[dict[str, Any]],
    model: str,
    concurrency: int,
    duplicate_schema: bool,
    json_mode: bool,
    score_next_question: bool,
) -> tuple[list[TurnScore], dict[str, str]]:
    semaphore = asyncio.Semaphore(max(1, concurrency))
    scores: list[TurnScore] = []
    raw_by_id: dict[str, str] = {}
    aborted: str | None = None

    async def worker(turn: dict[str, Any]) -> None:
        nonlocal aborted
        if aborted:
            return
        async with semaphore:
            if aborted:
                return
            try:
                score, raw = await run_turn(
                    client,
                    turn,
                    questions=questions,
                    model=model,
                    duplicate_schema=duplicate_schema,
                    json_mode=json_mode,
                    score_next_question=score_next_question,
                )
            except FatalRunError as exc:
                aborted = str(exc)
                return
        scores.append(score)
        raw_by_id[turn["id"]] = raw
        marker = "!" if score.error else ("." if score.schema_valid else "x")
        print(marker, end="", flush=True)

    await asyncio.gather(*(worker(turn) for turn in turns))
    print()
    if aborted:
        print(f"\nRun aborted: {aborted}", file=sys.stderr)
        print(f"Scored {len(scores)} of {len(turns)} turns before aborting.", file=sys.stderr)

    order = {turn["id"]: index for index, turn in enumerate(turns)}
    scores.sort(key=lambda s: order.get(s.turn_id, 0))
    return scores, raw_by_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="Row label for results.md")
    parser.add_argument("--model", default=settings.hf_model)
    parser.add_argument("--base-url", default=settings.hf_base_url)
    parser.add_argument("--api-key", default=None, help="Defaults to HF_TOKEN")
    parser.add_argument("--dataset", default=str(EVAL_DATASET_PATH))
    parser.add_argument("--questions", default=str(QUESTIONS_PATH))
    parser.add_argument("--split", choices=["dev", "holdout", "all"], default="dev")
    parser.add_argument("--category", default=None, help="Restrict to one category")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Keep at 1 for CPU serving; parallel requests contend for the same cores",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument(
        "--duplicate-schema",
        action="store_true",
        help="Also prepend the provider's schema copy, as intake did before P1",
    )
    parser.add_argument(
        "--no-json-mode",
        action="store_true",
        help="Do not send response_format=json_object",
    )
    parser.add_argument(
        "--no-next-question",
        action="store_true",
        help="Score next_question.key as n/a (use once the key leaves the schema)",
    )
    parser.add_argument("--out", default=None, help="Defaults to results/<label>.json")
    return parser


async def main_async(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    questions = load_questions(Path(args.questions))
    turns = load_dataset(Path(args.dataset))
    if args.split != "all":
        turns = [t for t in turns if t.get("split", "dev") == args.split]
    if args.category:
        turns = [t for t in turns if t.get("category") == args.category]
    if args.limit:
        turns = turns[: args.limit]
    if not turns:
        print("No turns selected.", file=sys.stderr)
        return 1

    api_key = args.api_key or settings.hf_token or "missing-api-key"
    client = AsyncOpenAI(base_url=args.base_url, api_key=api_key, timeout=args.timeout,
                         max_retries=0)

    # ASCII only: the default Windows console encoding (cp1252) cannot encode arrows.
    print(f"{args.label}: {len(turns)} turns -> {args.model} at {args.base_url}")
    scores, raw_by_id = await run_dataset(
        turns,
        client=client,
        questions=questions,
        model=args.model,
        concurrency=args.concurrency,
        duplicate_schema=args.duplicate_schema,
        json_mode=not args.no_json_mode,
        score_next_question=not args.no_next_question,
    )
    if not scores:
        return 1

    summary = aggregate(scores)
    categories = by_category(scores)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out) if args.out else RESULTS_DIR / f"{args.label}.json"
    out_path.write_text(
        json.dumps(
            {
                "label": args.label,
                "command": " ".join(sys.argv),
                "model": args.model,
                "base_url": args.base_url,
                "split": args.split,
                "duplicate_schema": args.duplicate_schema,
                "json_mode": not args.no_json_mode,
                "temperature": INTAKE_PARSE_TEMPERATURE,
                "max_tokens": INTAKE_PARSE_MAX_TOKENS,
                "summary": summary.__dict__,
                "by_category": {name: agg.__dict__ for name, agg in categories.items()},
                "turns": [
                    {**score.__dict__, "raw_output": raw_by_id.get(score.turn_id, "")}
                    for score in scores
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nWrote {out_path}\n")
    print("Paste into ml/eval/results.md:\n")
    print(markdown_row(args.label, args.model, args.base_url, summary))
    print("\nPer category (field F1 / value acc / skip recall):")
    for name, agg in categories.items():
        print(
            f"  {name:<20} {agg.turns:>3} turns  "
            f"{fmt(agg.fields.get('f1'))}  "
            f"{fmt(agg.value_accuracy)}  "
            f"{fmt(agg.skips.get('recall'))}"
        )
    if summary.invented_keys_total:
        print(f"\nKeys emitted outside the question set: {summary.invented_keys_total}")
    if summary.errors:
        print(f"Turns that errored: {summary.errors}")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
