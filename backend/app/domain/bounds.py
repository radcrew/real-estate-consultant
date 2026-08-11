"""Correct min/max direction on range criteria using the message's own comparator.

Which side of a range a figure belongs to is stated by a comparator, and reading a
comparator is exact — it does not need a language model. The tuned intake model gets it
wrong on wordings absent from its training set, in both directions: ``lower than $2M``
comes back as ``{"min": 2000000}`` and ``just shy of 8,000 sqft`` as ``{"min": 8000}``.

So the model keeps the parts that are genuinely hard — noticing a budget was mentioned,
reading ``$2M`` as ``2000000`` — and this decides the side.

The correction is deliberately timid. It fires only when the message states exactly one
direction and the model emitted exactly one bound; anything else is returned untouched,
because a wrong correction is worse than the model's own answer.
"""

from __future__ import annotations

import re
from typing import Any

# Ordered: negations, then multi-word forms, then single words. ``re`` scans left to
# right, so a negation starting earlier in the string consumes the comparator nested
# inside it — "no less than" is a lower bound despite containing "less than", and
# "nothing over" is an upper bound despite containing "over".
#
# ``floor`` and ``ceiling`` are deliberately absent. They read as bounds in a budget
# sentence but mean something else entirely in commercial real estate ("ground floor
# retail", "24 ft clear ceiling height"), and the model already handles both correctly.
# Comparative adjectives are matched as a class rather than one word at a time. Listing
# them individually is how "larger than 32 sqft" slipped through: the list had "greater
# than" and "higher than" but not the size-flavoured synonyms.
_MORE = r"(?:more|larger|bigger|greater|higher|longer|wider|taller|deeper|heavier)"
_LESS = r"(?:less|smaller|lower|shorter|narrower|slimmer|lighter)"

_BOUND_WORDS: list[tuple[str, str]] = [
    # Negations invert, so they must match before the comparative nested inside them.
    (rf"no\s+{_LESS}\s+than", "min"),
    (rf"not\s+{_LESS}\s+than", "min"),
    (rf"nothing\s+(?:below|under|{_LESS}\s+than)", "min"),
    (rf"no\s+{_MORE}\s+than", "max"),
    (rf"not\s+{_MORE}\s+than", "max"),
    (rf"nothing\s+(?:over|above|{_MORE}\s+than)", "max"),
    (r"not\s+(?:over|above|exceeding)", "max"),
    # Comparatives.
    (rf"{_MORE}\s+than", "min"),
    (rf"{_LESS}\s+than", "max"),
    # Multi-word.
    (r"at\s+least", "min"),
    (r"starting\s+at", "min"),
    (r"upwards\s+of", "min"),
    (r"north\s+of", "min"),
    (r"in\s+excess\s+of", "min"),
    (r"and\s+(?:up|over|above)\b", "min"),
    (r"or\s+(?:more|over|above)\b", "min"),
    (r"up\s+to", "max"),
    (r"at\s+most", "max"),
    (r"shy\s+of", "max"),
    (r"or\s+(?:less|under|below)\b", "max"),
    # Single words.
    (r"\bminimum\b", "min"),
    (r"\bexceeding\b", "min"),
    (r"\bover\b", "min"),
    (r"\babove\b", "min"),
    (r"\bbeyond\b", "min"),
    (r"\bmaximum\b", "max"),
    (r"\bunder\b", "max"),
    (r"\bbelow\b", "max"),
    (r"\bbeneath\b", "max"),
    (r"\btops\b", "max"),
    (r"\bcap(?:ped)?\b", "max"),
]

_BOUND_RE = re.compile(
    "|".join(f"(?P<g{index}>{pattern})" for index, (pattern, _) in enumerate(_BOUND_WORDS)),
    re.IGNORECASE,
)
_GROUP_SIDE = {f"g{index}": side for index, (_, side) in enumerate(_BOUND_WORDS)}


# "$1M" -> 1000000, "500k" -> 500000, "$2.5 million" -> 2500000, "100sqft" -> 100.
# The suffix needs a word boundary after it or "100 meters" would read as 100 million;
# the number itself must not, or "100sqft" would not parse at all.
_MULTIPLIERS = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mm": 1e6, "million": 1e6,
                "b": 1e9, "bn": 1e9, "billion": 1e9}
_NUMBER_RE = re.compile(
    r"\$?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?P<suffix>k\b|mm\b|m\b|bn\b|b\b|thousand\b|million\b|billion\b)?",
    re.IGNORECASE,
)

# How far a comparator may sit from the number it governs. Comfortably spans "no more
# than " and "$2M tops" without reaching across a clause.
_MAX_COMPARATOR_GAP = 24


def bound_sides_in(text: str) -> set[str]:
    """Return the bound directions the message states — a subset of ``{"min", "max"}``."""
    return {_GROUP_SIDE[match.lastgroup] for match in _BOUND_RE.finditer(text or "")}


def _numbers_in(text: str) -> list[tuple[int, int, float]]:
    found: list[tuple[int, int, float]] = []
    for match in _NUMBER_RE.finditer(text):
        try:
            value = float(match.group("num").replace(",", ""))
        except ValueError:
            continue
        if suffix := match.group("suffix"):
            value *= _MULTIPLIERS[suffix.lower()]
        found.append((match.start("num"), match.end(), value))
    return found


def numbers_with_direction(text: str) -> list[tuple[float, str | None]]:
    """Pair every figure in the message with the comparator that governs it.

    A whole-message reading cannot answer "lower than $2M, bigger than 100 sqft" — it
    sees both directions and can say nothing about either. Each figure takes the nearest
    comparator on either side (``up to $2M`` and ``$2M tops`` both occur), and a
    comparator may not reach across another figure to claim one further away.
    """
    numbers = _numbers_in(text or "")
    comparators = [
        (match.start(), match.end(), _GROUP_SIDE[match.lastgroup])
        for match in _BOUND_RE.finditer(text or "")
    ]

    paired: list[tuple[float, str | None]] = []
    for index, (start, end, value) in enumerate(numbers):
        previous_end = numbers[index - 1][1] if index else 0
        next_start = numbers[index + 1][0] if index + 1 < len(numbers) else len(text)

        best_side, best_gap = None, None
        for c_start, c_end, side in comparators:
            if c_end <= start:
                if c_end < previous_end:
                    continue  # governs an earlier figure
                gap = start - c_end
            elif c_start >= end:
                if c_start > next_start:
                    continue  # governs a later figure
                gap = c_start - end
            else:
                continue
            if gap <= _MAX_COMPARATOR_GAP and (best_gap is None or gap < best_gap):
                best_side, best_gap = side, gap
        paired.append((value, best_side))
    return paired


def _significant_digits(value: float) -> str:
    """The digits without their magnitude: 30000000 and 3000000 both give "3".

    13500 gives "135" and 1500 gives "15", so a square-yard conversion -- the one place
    the model is *supposed* to return a figure the message does not contain -- cannot be
    mistaken for a magnitude slip.
    """
    if value <= 0:
        return ""
    text = f"{value:.10f}".rstrip("0").rstrip(".").replace(".", "")
    return text.strip("0") or "0"


def _rescaled(bound: float, figures: list[tuple[float, str | None]]):
    """A message figure differing from ``bound`` only in magnitude, nearest one first.

    The 0.5B reads a large budget correctly and then writes it short. Measured on the
    served Q4, stock and tuned alike, every miss keeps the significant digits and loses
    zeros: "$30M" -> 3,000,000, "$150M" -> 1,500,000, "$45,000,000" -> 4,500,000. The
    largest value it produced anywhere on a magnitude ladder was 9,500,000.

    Equal significant digits at different values already implies the two are a power of
    ten apart, so there is nothing further to check.

    **Exactly one candidate, or nothing.** Two figures sharing a bound's digits mean the
    message cannot say which was mis-sized, and guessing turns a dropped field into a
    wrong one. "costs less than $1M, size is bigger than 100sqft" is the case: the model
    invents ``size_sqft.max = 10000``, whose digits match both 1000000 and 100, and the
    invented bound has to stay droppable. Nearest-wins picked one of the two and stored a
    10,000x error.
    """
    digits = _significant_digits(bound)
    if not digits:
        return None
    candidates = [f for f in figures if f[0] != bound and _significant_digits(f[0]) == digits]
    return candidates[0] if len(candidates) == 1 else None


def _correct_one(value: dict[str, Any], figures: list[tuple[float, str | None]]) -> dict[str, Any]:
    """Rebuild one range value from the figures the message actually contains."""
    stated = {side: value[side] for side in ("min", "max") if value.get(side) is not None}
    if not stated:
        return value

    rebuilt: dict[str, Any] = {}
    matched_any = False
    for side, bound in stated.items():
        try:
            numeric = float(bound)
        except (TypeError, ValueError):
            rebuilt[side] = bound
            matched_any = True
            continue
        match = next((f for f in figures if f[0] == numeric), None)
        if match is None:
            # Before calling it invented: the same digits at another magnitude means the
            # model read the figure and mis-sized it, and the message settles the size.
            match = _rescaled(numeric, figures)
            if match is None:
                continue  # no figure in the message supports this bound: invented
            bound = int(match[0]) if float(match[0]).is_integer() else match[0]
        matched_any = True
        rebuilt[match[1] or side] = bound

    # Nothing matched at all — the model may have normalised a figure this cannot parse
    # ("half a million"), so its answer stands.
    return rebuilt if matched_any and rebuilt else value


def correct_bound_direction(extracted: dict[str, Any], user_input: str) -> dict[str, Any]:
    """Put each range bound on the side its own figure's comparator indicates.

    Two failures, one cause. The model puts a stated bound on the wrong side ("lower than
    $2M" → ``{"min": 2000000}``), and it invents the opposite bound to fill the shape
    ("less than $1M" → ``{"min": 0, "max": 1000000}``). Both are settled by asking which
    figure in the message each bound came from.

    A bound whose value appears nowhere in the message was not stated, so it is dropped.
    A bound whose figure carries a comparator moves to that side. If no bound matches any
    figure the value is returned untouched, so an unparseable figure costs coverage
    rather than correctness.
    """
    figures = numbers_with_direction(user_input)
    if not figures:
        return extracted

    corrected = dict(extracted)
    for key, value in extracted.items():
        if isinstance(value, dict):
            corrected[key] = _correct_one(value, figures)
    return corrected
