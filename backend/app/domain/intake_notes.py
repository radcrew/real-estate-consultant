"""Explain what the system did to the user's own words.

Between what someone types and what the search runs on there are four silent
transformations, and until now every one of them happened without a word:

    "I need a 100k yard farm"   -> size 900,000 sq ft      (a unit converted)
    "a 100k sqft warehouse"     -> no budget recorded      (a figure reassigned)
    "under $2M"                 -> price max 2,000,000     (a bound moved)
    "up to $30M"                -> price max 30,000,000    (a magnitude corrected)

Each is correct and none of them is obvious. Someone who wrote "100k yard" and is shown
900,000 sq ft has no way to tell a right answer from a bug, and the reply they got was
"You're all set!" — which reads as the system ignoring what they asked for. The cost of
silence is not a wrong search, it is a user who no longer believes the right one.

So this states the transformation in the user's own terms, beside the value it produced.

Two rules keep it honest:

**Only say what is certainly true.** A note is emitted when the arithmetic is checked
against both sides — the figure in the message and the value in the criteria — not when
one is merely plausible. A wrong explanation is worse than none, because it teaches
someone to distrust the ones that are right.

**Never explain the ordinary.** A size given in sqft and stored in sqft produces no note.
Explaining every field would bury the one line that matters in a paragraph nobody reads.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.bounds import _FIELD_KINDS, numbers_with_direction, same_significant_digits
from app.domain.intake_vocabulary import AREA_UNITS

# Relative slack when checking a conversion. Square metres are 10.7639 sq ft and the model
# rounds the product, so an exact comparison would reject every metric conversion.
_CONVERSION_TOLERANCE = 0.005

_SIZE_FIELD = "size_sqft"
_NOT_ALNUM = re.compile(r"[^a-z0-9]")

# Which field a figure of each kind belongs to, for saying where a dropped one went.
_KIND_OWNER = {kind: field for field, kind in _FIELD_KINDS.items()}
_KIND_NAMES = {
    "area": "a size", "money": "a budget", "length": "a height or length",
    "count": "a count", "share": "a percentage", "term": "a period",
}


def _compact(unit: str) -> str:
    return _NOT_ALNUM.sub("", unit.lower())


def _number(value: float) -> str:
    """A figure as a person would write it, without a trailing ``.0``."""
    return f"{int(value):,}" if float(value).is_integer() else f"{value:,.2f}"


def _bounds(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out = {}
    for side in ("min", "max"):
        raw = value.get(side)
        if raw is None:
            continue
        try:
            out[side] = float(raw)
        except (TypeError, ValueError):
            continue
    return out


def _note(field: str, kind: str, message: str) -> dict[str, str]:
    return {"field": field, "kind": kind, "message": message}


def _conversion_notes(figures, criteria) -> list[dict[str, str]]:
    """A size the user gave in yards, metres or acres, and what it became."""
    stored = _bounds(criteria.get(_SIZE_FIELD))
    if not stored:
        return []
    notes = []
    seen: set[tuple[float, float]] = set()
    for figure in figures:
        if figure.kind != "area" or not figure.unit:
            continue
        entry = AREA_UNITS.get(_compact(figure.unit))
        if entry is None or entry[0] == 1.0:
            continue  # already square feet, or a unit this cannot convert
        factor, name = entry
        converted = figure.value * factor
        tolerance = max(1.0, converted * _CONVERSION_TOLERANCE)
        if not any(abs(bound - converted) <= tolerance for bound in stored.values()):
            continue  # the stored size is not this conversion, so do not claim it is
        if (figure.value, factor) in seen:
            continue
        seen.add((figure.value, factor))
        plural = f"{name}s" if not name.endswith("s") else name
        notes.append(_note(
            _SIZE_FIELD, "converted",
            f"You gave the size as {_number(figure.value)} {plural}. "
            f"Search works in square feet, so I recorded "
            f"{_number(round(converted))} sq ft "
            f"({_number(round(factor, 2))} sq ft per {name}).",
        ))
    return notes


def _titles(questions: list[dict[str, Any]] | None) -> dict[str, str]:
    """Field key to the name the questionnaire gives it.

    ``questions.json`` holds the wording everywhere else in intake, for the same reason it
    should here: "your Size" is the phrase the user was shown, and "your size_sqft" is a
    column name leaking into a sentence.
    """
    named = {}
    for row in questions or []:
        key, title = row.get("key"), row.get("title")
        if isinstance(key, str) and isinstance(title, str) and title.strip():
            named[key] = title.strip()
    return named


def _reassignment_notes(figures, model_extracted, criteria, titles) -> list[dict[str, str]]:
    """A figure the model put in one field that the message measures in another."""
    notes = []
    for field, value in model_extracted.items():
        if field in criteria or field not in _FIELD_KINDS:
            continue
        wanted = _FIELD_KINDS[field]
        for bound in _bounds(value).values():
            match = next(
                (f for f in figures
                 if f.value == bound and f.kind is not None and f.kind != wanted),
                None,
            )
            if match is None:
                continue
            owner = _KIND_OWNER.get(match.kind)
            described = _KIND_NAMES.get(match.kind, "something else")
            tail = ""
            if owner and owner in criteria:
                name = titles.get(owner, owner.replace("_", " "))
                tail = f" It is recorded as your {name}."
            notes.append(_note(
                field, "reassigned",
                f"{_number(bound)} in your message is {described}, not "
                f"{_KIND_NAMES.get(wanted, 'this')}, so I have not used it here.{tail}",
            ))
            break
    return notes


# How a field's values read in a sentence, so a range is not printed as raw JSON.
_FIELD_UNITS = {"price": ("$", ""), "size_sqft": ("", " sq ft")}


def _readable(field: str, value: Any) -> str | None:
    """One field's value as a person would say it, or None if it cannot be phrased."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or None
    if isinstance(value, str):
        return value.strip() or None
    bounds = _bounds(value)
    if not bounds:
        return None
    prefix, suffix = _FIELD_UNITS.get(field, ("", ""))

    def one(bound: float) -> str:
        return f"{prefix}{_number(bound)}{suffix}"

    low, high = bounds.get("min"), bounds.get("max")
    if low is not None and high is not None:
        return one(low) if low == high else f"{one(low)} to {one(high)}"
    if low is not None:
        return f"at least {one(low)}"
    return f"up to {one(high)}"


def _replacement_notes(extracted, current_criteria, titles) -> list[dict[str, str]]:
    """A value this turn overwrote, and what it used to be.

    A correction is legitimate -- "actually I was wrong, now I need 100 yard one" means
    what it says, and the questionnaire supports changing an earlier answer. Doing it
    without a word is what is not: a size established as 100,000 sq ft becoming 900 is a
    111x change, and until now the only thing on screen was arithmetic about yards.

    So the change is applied and stated. Silence here is the same failure as silence about
    a conversion, one field further along.
    """
    notes = []
    for field, value in extracted.items():
        if field not in current_criteria:
            continue  # a first answer, not a replacement
        was, now = _readable(field, current_criteria[field]), _readable(field, value)
        if was is None or now is None or was == now:
            continue
        name = titles.get(field, field.replace("_", " "))
        notes.append(_note(
            field, "replaced",
            f"Your {name} was {was}; it is now {now}.",
        ))
    return notes


def _correction_notes(model_extracted, criteria) -> list[dict[str, str]]:
    """A bound the wording moved to the other side, or a magnitude the message settled."""
    notes = []
    for field, value in criteria.items():
        final = _bounds(value)
        before = _bounds(model_extracted.get(field))
        if not final or not before:
            continue
        for side, bound in final.items():
            if before.get(side) == bound:
                continue
            other = "min" if side == "max" else "max"
            if before.get(other) == bound:
                notes.append(_note(
                    field, "moved",
                    f"Your wording puts {_number(bound)} as "
                    f"{'an upper' if side == 'max' else 'a lower'} limit, so that is "
                    "where I recorded it.",
                ))
                continue
            was = before.get(side)
            if was is not None and was != bound and same_significant_digits(was, bound):
                notes.append(_note(
                    field, "resized",
                    f"I recorded {_number(bound)}, matching the figure in your message.",
                ))
    return notes


def explain_extraction(
    user_input: str,
    model_extracted: dict[str, Any],
    criteria: dict[str, Any],
    questions: list[dict[str, Any]] | None = None,
    current_criteria: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Plain-language notes on every transformation between the message and the criteria.

    ``model_extracted`` is the reply before the filters and ``criteria`` is what the
    session stored, so the difference between them is exactly what needs explaining.

    Returns an empty list for the ordinary case, which is most of them.
    """
    titles = _titles(questions)
    # A replacement is worth stating whether or not the turn contained a figure: changing
    # the location from Chicago to Dallas is the same kind of surprise as changing a size.
    replaced = _replacement_notes(criteria, current_criteria or {}, titles)
    figures = numbers_with_direction(user_input or "")
    if not figures:
        return replaced
    return [
        *replaced,
        *_conversion_notes(figures, criteria),
        *_reassignment_notes(figures, model_extracted, criteria, titles),
        *_correction_notes(model_extracted, criteria),
    ]
