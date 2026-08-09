"""Generate natural phrasings for each configured property type, asked of a model.

    cd backend
    python -m ml.data.make_phrasings --base-url https://openrouter.ai/api/v1 \
      --api-key "$OPENROUTER_API_KEY" --model qwen/qwen-2.5-7b-instruct

The tuned intake model echoes the user's noun into ``property_type`` — "warehouse", "shop",
"apartment block" — so the value is not a configured option and gets dropped, leaving the
field unanswered. Every ``property_type`` example in ``ml.data.generate`` renders the option
word itself, so across ~2160 examples not one has a message word differing from its gold
word. The most reinforced rule in the set is *copy the noun you see*.

This writes the vocabulary that breaks that: phrasings a client would actually use, paired
with the option they mean. Gold stays the option; only the wording varies. The list is
generated, never hand-maintained, so changing the questionnaire and re-running keeps it
correct.

**Use a model that knows the mappings.** Each candidate is validated by asking the same
model to map it back, so a proposer that is wrong will also validate itself as right. The
0.5B scores 3-4 of 6 on this question — it answers ``factory -> Office`` — and would
generate wrong pairs and confirm them. The 7B mapped all six probe words correctly.

Output is a build artifact: gitignored, regenerated rather than edited.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.supabase_sdk import close_supabase, get_supabase_sdk_client, init_supabase
from app.repositories.questions import list_intake_questions
from ml.data.generate import property_type_values

ML_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ML_DIR / "data" / "property_type_phrasings.json"

ASK = (
    "List {n} different words or short phrases a commercial real-estate client might use "
    "when they mean a {option} property. Everyday wording, not jargon. "
    "One per line, no numbering, no explanation."
)
CHECK = "which of these is closest to {phrase}?\n{options}\njust gimme answer, no need to explain"

_LEAD = re.compile(r"^[\s\-*•\d.)]+")
_WORD = re.compile(r"[a-z]+")


# Curly quotes and dashes arrive from the model and would become odd training tokens,
# besides being unprintable on a cp1252 console. Fold the common ones, drop the rest.
_UNICODE_FOLD = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                               "–": "-", "—": "-", "…": "", " ": " "})


def _clean(line: str) -> str | None:
    text = _LEAD.sub("", line).translate(_UNICODE_FOLD)
    text = text.strip().strip('"').strip("'").lower()
    # Drop preamble ("here are 14 ...") and anything too long to be a search term.
    if not (2 <= len(text) <= 40) or text.endswith(":"):
        return None
    if not text.isascii():
        return None
    return text


def _answer_matches(reply: str, option: str) -> bool:
    """True when the model's answer names ``option`` first.

    Answers arrive as "Industrial", "Industrial.", "Land\n" and occasionally a short
    sentence, so compare the first alphabetic token rather than the whole string.
    """
    tokens = _WORD.findall((reply or "").lower())
    return bool(tokens) and tokens[0] == option.lower()


async def propose(client: AsyncOpenAI, model: str, option: str, count: int) -> list[str]:
    reply = await client.chat.completions.create(
        model=model, temperature=0.8, max_tokens=250,
        messages=[{"role": "user", "content": ASK.format(n=count, option=option)}],
    )
    seen: list[str] = []
    for line in (reply.choices[0].message.content or "").splitlines():
        if (text := _clean(line)) and text not in seen:
            seen.append(text)
    return seen


async def round_trips(
    client: AsyncOpenAI, model: str, phrase: str, option: str, options: list[str]
) -> bool:
    """Keep a phrase only if the model maps it back to the option it was generated for."""
    reply = await client.chat.completions.create(
        model=model, temperature=0, max_tokens=12,
        messages=[{"role": "user", "content": CHECK.format(
            phrase=phrase, options=", ".join(o.capitalize() for o in options))}],
    )
    return _answer_matches(reply.choices[0].message.content or "", option)


async def main_async(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://openrouter.ai/api/v1")
    parser.add_argument("--api-key", default=None, help="Defaults to OPENROUTER_API_KEY")
    parser.add_argument("--model", default="qwen/qwen-2.5-7b-instruct")
    parser.add_argument("--per-option", type=int, default=14)
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    await init_supabase()
    try:
        questions = await list_intake_questions(get_supabase_sdk_client())
    finally:
        await close_supabase()
    options = property_type_values(questions)

    api_key = args.api_key or settings.openrouter_api_key
    if not api_key:
        raise SystemExit("no API key: pass --api-key or set OPENROUTER_API_KEY")

    client = AsyncOpenAI(base_url=args.base_url, api_key=api_key, timeout=120, max_retries=0)
    print(f"asking {args.model} for {args.per_option} phrasings per option\n")

    phrasings: dict[str, list[str]] = {}
    for option in options:
        proposed = await propose(client, args.model, option, args.per_option)
        # An option word is not a phrasing for itself, and a candidate claimed by two
        # options is ambiguous — both would put a wrong label on a training example.
        candidates = [p for p in proposed if p not in options]
        checks = await asyncio.gather(
            *(round_trips(client, args.model, p, option, options) for p in candidates)
        )
        kept = [p for p, ok in zip(candidates, checks) if ok]
        phrasings[option] = kept
        print(f"  {option:<12} proposed {len(proposed):>2}  kept {len(kept):>2}  {kept}")
    await client.close()

    claimed: dict[str, str] = {}
    for option, words in phrasings.items():
        for word in words:
            if word in claimed:
                print(f"  dropping {word!r}: claimed by both {claimed[word]} and {option}")
                phrasings[option] = [w for w in phrasings[option] if w != word]
            else:
                claimed[word] = option

    out = Path(args.out)
    out.write_text(json.dumps(phrasings, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    total = sum(len(v) for v in phrasings.values())
    print(f"\nwrote {total} phrasings across {len(phrasings)} options -> {out}")
    if thin := [o for o, v in phrasings.items() if len(v) < 4]:
        print(f"WARNING thin coverage for {thin}: raise --per-option or use a stronger model")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
