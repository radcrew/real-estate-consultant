"""Scoring for intake extraction eval runs.

Pure functions only — no network, no config, no model. Everything here is unit-tested in
``ml/intake-parser/tests/test_eval_metrics.py`` so a metric change is a visible diff rather
than a silently different number in a results table.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from app.schemas.llm_intake_parse import LlmParseModelOutput

# Value comparison ------------------------------------------------------------------


def normalize_value(value: Any) -> Any:
    """Reduce a criteria value to a hashable, comparable form.

    Strings are case- and whitespace-insensitive, numbers unify int and float, lists are
    order-insensitive, and ``None`` bounds inside an object are treated as absent so
    ``{"min": null, "max": 5}`` and ``{"max": 5}`` compare equal.
    """
    if value is None:
        return ("null", None)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        return ("num", float(value))
    if isinstance(value, str):
        return ("str", " ".join(value.split()).casefold().strip(" .,"))
    if isinstance(value, list):
        return ("list", frozenset(normalize_value(item) for item in value))
    if isinstance(value, dict):
        return (
            "dict",
            frozenset(
                (key, normalize_value(val)) for key, val in value.items() if val is not None
            ),
        )
    return ("other", repr(value))


def values_equal(expected: Any, actual: Any) -> bool:
    """True when two criteria values agree under :func:`normalize_value`."""
    return normalize_value(expected) == normalize_value(actual)


# Per-turn scoring ------------------------------------------------------------------


@dataclass(frozen=True)
class TurnScore:
    """Everything measured about one eval turn."""

    turn_id: str
    category: str
    raw_json_valid: bool = False
    schema_valid: bool = False
    field_tp: int = 0
    field_fp: int = 0
    field_fn: int = 0
    invented_keys: int = 0
    value_correct: int = 0
    value_compared: int = 0
    skip_tp: int = 0
    skip_fp: int = 0
    skip_fn: int = 0
    next_question_correct: bool | None = None
    latency_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    error: str | None = None


def parse_raw_output(raw_text: str) -> tuple[bool, bool, LlmParseModelOutput | None]:
    """Return (raw JSON parsed, validated against the schema, parsed model).

    Deliberately does **not** use the provider's fence-stripper: raw validity is the
    number we want, and ``_extract_json_object`` would hide a model that wraps its reply
    in markdown or pads it with commentary.

    Only ``ValidationError`` counts as schema-invalid. A bare ``except Exception`` here
    would fold a broken ``LlmParseModelOutput`` -- a renamed field, a bad annotation --
    into ``schema_valid=False`` on every turn, and the run would finish and write a
    plausible-looking table of zeros rather than failing.
    """
    try:
        json.loads(raw_text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return False, False, None

    try:
        return True, True, LlmParseModelOutput.model_validate_json(raw_text)
    except ValidationError:
        return True, False, None


def score_turn(
    *,
    turn_id: str,
    category: str,
    gold: dict[str, Any],
    predicted: LlmParseModelOutput | None,
    required_fields: list[str],
    question_keys: list[str],
    raw_json_valid: bool,
    schema_valid: bool,
    latency_ms: float,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    score_next_question: bool = True,
    error: str | None = None,
) -> TurnScore:
    """Score one turn's prediction against its gold record."""
    base = {
        "turn_id": turn_id,
        "category": category,
        "raw_json_valid": raw_json_valid,
        "schema_valid": schema_valid,
        "latency_ms": latency_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "error": error,
    }
    if predicted is None:
        # Unparseable output scores as a miss on every gold field, never as a pass.
        gold_extracted = gold.get("extracted") or {}
        gold_skips = set(gold.get("skipped_fields") or []) & set(required_fields)
        return TurnScore(
            **base,
            field_fn=len(gold_extracted),
            skip_fn=len(gold_skips),
            next_question_correct=False if score_next_question else None,
        )

    gold_extracted = gold.get("extracted") or {}
    pred_extracted = predicted.extracted or {}
    gold_keys = set(gold_extracted)
    pred_keys = set(pred_extracted)
    allowed = set(question_keys)

    matched = gold_keys & pred_keys
    value_correct = sum(
        1 for key in matched if values_equal(gold_extracted[key], pred_extracted[key])
    )

    required = set(required_fields)
    gold_skips = set(gold.get("skipped_fields") or []) & required
    pred_skips = set(predicted.skipped_fields or []) & required

    next_correct: bool | None = None
    if score_next_question:
        gold_next = gold.get("next_question_key")
        pred_next = predicted.next_question.key if predicted.next_question else None
        next_correct = gold_next == pred_next

    return TurnScore(
        **base,
        field_tp=len(matched),
        field_fp=len(pred_keys - gold_keys),
        field_fn=len(gold_keys - pred_keys),
        invented_keys=len(pred_keys - allowed),
        value_correct=value_correct,
        value_compared=len(matched),
        skip_tp=len(gold_skips & pred_skips),
        skip_fp=len(pred_skips - gold_skips),
        skip_fn=len(gold_skips - pred_skips),
        next_question_correct=next_correct,
    )


# Aggregation -----------------------------------------------------------------------


def ratio(numerator: int, denominator: int) -> float | None:
    """Return the ratio, or ``None`` when undefined — never a misleading 0.0."""
    if denominator <= 0:
        return None
    return numerator / denominator


def prf(tp: int, fp: int, fn: int) -> dict[str, float | None]:
    """Precision, recall and F1, each ``None`` where its denominator is empty.

    ``None`` means *not measured*; ``0.0`` means *measured, and nothing was right*. The
    two must not be confused, because the second is the worst possible score and the first
    is no score at all.

    F1 followed that rule for its inputs and then broke it for itself: ``precision + recall
    == 0`` short-circuited to ``None`` alongside the genuinely-undefined cases, so a
    candidate that predicted keys and got every one of them wrong -- both rates defined,
    both exactly 0.0 -- reported its collapse as "not measured". Two recorded runs carry
    that on their ``complete`` category. The guard is only needed to avoid dividing by
    zero, and the value at that limit is 0.0.
    """
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    if precision is None or recall is None:
        f1 = None
    elif precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile: the smallest value at or above ``p`` percent. ``p`` in [0, 100].

    ``ceil``, not ``round(k + 0.5)`` — the latter is round-half-to-even, so an exact
    integer ``k`` returned rank ``k + 1``. That skewed every percentile whose rank landed
    on a whole number, which for an even-sized run is every p50.

    ``p * n / 100`` rather than ``p / 100 * n`` keeps the multiplication in exact integers
    for whole ``p``, so ``ceil`` is not decided by a float that missed by one ulp.
    """
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), math.ceil(p * len(ordered) / 100)))
    return ordered[rank - 1]


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


@dataclass
class Aggregate:
    """Summary across a run, with every rate defined or explicitly ``None``."""

    turns: int = 0
    errors: int = 0
    raw_json_valid_rate: float | None = None
    schema_valid_rate: float | None = None
    fields: dict[str, float | None] = field(default_factory=dict)
    value_accuracy: float | None = None
    skips: dict[str, float | None] = field(default_factory=dict)
    invented_keys_total: int = 0
    next_question_accuracy: float | None = None
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    mean_prompt_tokens: float | None = None
    mean_completion_tokens: float | None = None


def aggregate(scores: list[TurnScore]) -> Aggregate:
    """Roll per-turn scores into one summary row."""
    if not scores:
        return Aggregate()

    scored_next = [s.next_question_correct for s in scores if s.next_question_correct is not None]
    latencies = [s.latency_ms for s in scores if s.latency_ms > 0]

    return Aggregate(
        turns=len(scores),
        errors=sum(1 for s in scores if s.error),
        raw_json_valid_rate=ratio(sum(1 for s in scores if s.raw_json_valid), len(scores)),
        schema_valid_rate=ratio(sum(1 for s in scores if s.schema_valid), len(scores)),
        fields=prf(
            sum(s.field_tp for s in scores),
            sum(s.field_fp for s in scores),
            sum(s.field_fn for s in scores),
        ),
        value_accuracy=ratio(
            sum(s.value_correct for s in scores),
            sum(s.value_compared for s in scores),
        ),
        skips=prf(
            sum(s.skip_tp for s in scores),
            sum(s.skip_fp for s in scores),
            sum(s.skip_fn for s in scores),
        ),
        invented_keys_total=sum(s.invented_keys for s in scores),
        next_question_accuracy=ratio(sum(1 for c in scored_next if c), len(scored_next)),
        latency_p50_ms=percentile(latencies, 50),
        latency_p95_ms=percentile(latencies, 95),
        mean_prompt_tokens=_mean([s.prompt_tokens for s in scores if s.prompt_tokens]),
        mean_completion_tokens=_mean([s.completion_tokens for s in scores if s.completion_tokens]),
    )


def by_category(scores: list[TurnScore]) -> dict[str, Aggregate]:
    """Per-category aggregates, for finding which turn kind a model fails on."""
    buckets: dict[str, list[TurnScore]] = {}
    for score in scores:
        buckets.setdefault(score.category, []).append(score)
    return {name: aggregate(rows) for name, rows in sorted(buckets.items())}


# Formatting ------------------------------------------------------------------------


def fmt(value: float | None, places: int = 3) -> str:
    """Render a metric, or ``n/a`` when it was never defined."""
    if value is None:
        return "n/a"
    return f"{value:.{places}f}"


def markdown_row(label: str, model: str, endpoint: str, summary: Aggregate) -> str:
    """One row for the results table in ``results.md``."""
    cells = [
        label,
        f"`{model}`",
        endpoint,
        str(summary.turns),
        fmt(summary.raw_json_valid_rate),
        fmt(summary.fields.get("precision")),
        fmt(summary.fields.get("recall")),
        fmt(summary.fields.get("f1")),
        fmt(summary.value_accuracy),
        fmt(summary.skips.get("precision")),
        fmt(summary.skips.get("recall")),
        fmt(summary.next_question_accuracy),
        fmt(summary.latency_p50_ms, 0),
        fmt(summary.latency_p95_ms, 0),
    ]
    return "| " + " | ".join(cells) + " |"
