"""Rebuild range criteria from the figures, comparators and units the message contains.

Which side of a range a figure belongs to is stated by a comparator, and which field a
figure belongs to is stated by its unit. Reading either is exact — it does not need a
language model. The tuned intake model gets both wrong on wordings absent from its
training set: ``lower than $2M`` comes back as ``{"min": 2000000}``, ``just shy of 8,000
sqft`` as ``{"min": 8000}``, and ``a 100k sqft warehouse`` as a *budget* of 100000
alongside the size, because 100000 is genuinely in the message.

So the model keeps the parts that are genuinely hard — noticing a budget was mentioned,
reading ``$2M`` as ``2000000`` — and this decides the side and the owner. The invariant
being enforced is::

    FINAL_VALUE(field) requires EVIDENCE(field, user_message)

where evidence for a range field is a figure whose unit fits it.

The correction is deliberately timid, and one-directional where it is not sure: a field
left unanswered is asked again by the questionnaire, whereas a field wrongly filled in is
never asked and silently filters the search. So silence in the message means the model's
own answer stands, and only a figure the message positively assigns elsewhere is taken as
grounds to drop one.
"""

from __future__ import annotations

import re
from typing import Any, NamedTuple

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


# What a figure is measured in, read from the text immediately after it. This is what
# separates "100k sqft" from "$100k": the digits are identical and the unit is not.
#
# Order matters twice. Area comes before length because "sqft" has "ft" nested inside it,
# and "32ft clear height" is a length while "100k sqft" is an area. Within a kind, longer
# forms come first for the same reason.
#
# A figure whose unit is absent is left unclassified rather than guessed at. "budget up to
# 100k" says nothing after the figure, and an unclassified figure is evidence for any
# field — the message gave no grounds to rule one out, so the model's reading is the only
# reading available.
_UNIT_KINDS: list[tuple[str, str]] = [
    (r"sq(?:uare)?\s*\.?\s*(?:ft|feet|foot)\b", "area"),
    (r"sq(?:uare)?\s*\.?\s*(?:metres?|meters?|m)\b", "area"),
    (r"sq(?:uare)?\s*\.?\s*(?:yards?|yds?)\b", "area"),
    (r"(?:sqft|sqm|sf)\b", "area"),
    (r"(?:yards?|yds?|acres?)\b", "area"),
    (r"(?:dollars?|usd|bucks)\b", "money"),
    (r"(?:ft|feet|foot|metres?|meters?|inch(?:es)?)\b", "length"),
    (r"(?:dock\s+)?doors?\b", "count"),
    (r"(?:loading\s+)?(?:bays?|docks?)\b", "count"),
    (r"(?:parking\s+)?spaces?\b", "count"),
    (r"(?:freight\s+)?(?:lifts?|elevators?)\b", "count"),
    (r"(?:floors?|stor(?:ey|y|ie)s?|units?|suites?|offices?|rooms?|desks?|seats?)\b",
     "count"),
    (r"(?:%|(?:percent|pct)\b)", "share"),
    (r"(?:years?|months?|weeks?|days?|miles?|minutes?)\b", "term"),
]
_UNIT_RE = re.compile(
    r"\s*(?:"
    + "|".join(f"(?P<u{index}>{pattern})" for index, (pattern, _) in enumerate(_UNIT_KINDS))
    + r")",
    re.IGNORECASE,
)
_UNIT_GROUP_KIND = {f"u{index}": kind for index, (_, kind) in enumerate(_UNIT_KINDS)}

# The unit a field is measured in. A field absent here accepts any figure, so growing the
# questionnaire cannot silently start dropping values — ``questions.json`` has exactly two
# range fields today, and a third would arrive unrestricted until it is listed.
_FIELD_KINDS = {"price": "money", "size_sqft": "area"}


class _Figure(NamedTuple):
    """One figure in the message: what it says, which way, and what it measures."""

    value: float
    side: str | None
    kind: str | None


def bound_sides_in(text: str) -> set[str]:
    """Return the bound directions the message states — a subset of ``{"min", "max"}``."""
    return {_GROUP_SIDE[match.lastgroup] for match in _BOUND_RE.finditer(text or "")}


def _kind_of(text: str, match: re.Match[str]) -> str | None:
    """What a matched figure is measured in, or ``None`` if the message does not say.

    Money is written in front of the figure and every other unit behind it, so the "$" is
    read from the span ``_NUMBER_RE`` consumed ahead of the digits and the rest from the
    text immediately following the match.
    """
    if "$" in text[match.start():match.start("num")]:
        return "money"
    unit = _UNIT_RE.match(text, match.end())
    return _UNIT_GROUP_KIND[unit.lastgroup] if unit else None


def _numbers_in(text: str) -> list[tuple[int, int, float, str | None]]:
    found: list[tuple[int, int, float, str | None]] = []
    for match in _NUMBER_RE.finditer(text):
        try:
            value = float(match.group("num").replace(",", ""))
        except ValueError:
            continue
        if suffix := match.group("suffix"):
            value *= _MULTIPLIERS[suffix.lower()]
        found.append((match.start("num"), match.end(), value, _kind_of(text, match)))
    return found


def numbers_with_direction(text: str) -> list[_Figure]:
    """Pair every figure in the message with the comparator and unit that govern it.

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

    paired: list[_Figure] = []
    for index, (start, end, value, kind) in enumerate(numbers):
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
        paired.append(_Figure(value, best_side, kind))
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


def _fits(figure: _Figure, kind: str | None) -> bool:
    """Whether ``figure`` can be evidence for a field measured in ``kind``.

    Silence on either side permits: a field with no declared unit takes any figure, and a
    figure with no unit is available to any field.
    """
    return kind is None or figure.kind is None or figure.kind == kind


def _claimed(stated: dict[str, Any], figures: list[_Figure]) -> set[float]:
    """Figure values some stated bound already matches exactly.

    A figure spoken for by one bound is not also the mis-sized original of another. "size
    is bigger than 100sqft" with ``{"min": 100, "max": 10000}`` holds one figure and two
    bounds, and 100 belongs to the bound that matches it outright — which is what keeps
    the invented 10,000 from being "corrected" to the 100 standing right beside it.
    """
    values = {figure.value for figure in figures}
    claimed = set()
    for bound in stated.values():
        try:
            numeric = float(bound)
        except (TypeError, ValueError):
            continue
        if numeric in values:
            claimed.add(numeric)
    return claimed


def _rescaled(bound: float, figures: list[_Figure], kind: str | None, claimed: set[float]):
    """A message figure differing from ``bound`` only in magnitude, nearest one first.

    The 0.5B reads a large budget correctly and then writes it short. Measured on the
    served Q4, stock and tuned alike, every miss keeps the significant digits and loses
    zeros: "$30M" -> 3,000,000, "$150M" -> 1,500,000, "$45,000,000" -> 4,500,000. The
    largest value it produced anywhere on a magnitude ladder was 9,500,000.

    Equal significant digits at different values already implies the two are a power of
    ten apart, so there is nothing further to check.

    **Exactly one candidate, or nothing.** Two figures sharing a bound's digits mean the
    message cannot say which was mis-sized, and guessing turns a dropped field into a
    wrong one. "between $30M and $300M" is the case: a bound of 3,000,000 has the digits
    of both, both are money, and neither is spoken for. Nearest-wins picked one and stored
    a 100x error.

    A candidate must also be measured in this field's unit and not already claimed by
    another bound, which is what leaves "costs less than $1M, size is bigger than 100sqft"
    with no candidate at all for its invented ``size_sqft.max = 10000``: 1,000,000 is
    money and 100 is already the min.
    """
    digits = _significant_digits(bound)
    if not digits:
        return None
    candidates = [
        figure for figure in figures
        if figure.value != bound
        and figure.value not in claimed
        and _fits(figure, kind)
        and _significant_digits(figure.value) == digits
    ]
    return candidates[0] if len(candidates) == 1 else None


def _correct_one(
    value: dict[str, Any], figures: list[_Figure], kind: str | None
) -> dict[str, Any] | None:
    """Rebuild one range value from the figures the message actually contains.

    Returns ``None`` when every stated bound belongs to a different field, so the caller
    can drop the key rather than store an empty range.
    """
    stated = {side: value[side] for side in ("min", "max") if value.get(side) is not None}
    if not stated:
        return value

    claimed = _claimed(stated, figures)
    rebuilt: dict[str, Any] = {}
    ruled_out = False
    for side, bound in stated.items():
        try:
            numeric = float(bound)
        except (TypeError, ValueError):
            rebuilt[side] = bound
            continue
        match = next(
            (f for f in figures if f.value == numeric and _fits(f, kind)), None
        )
        if match is None:
            if any(f.value == numeric for f in figures):
                # The figure is in the message, measured in something this field cannot
                # be measured in — "100k sqft" is not a budget. That is evidence against
                # the bound rather than silence about it, so it does not get the benefit
                # of the doubt the next branch gives.
                ruled_out = True
                continue
            # Before calling it invented: the same digits at another magnitude means the
            # model read the figure and mis-sized it, and the message settles the size.
            match = _rescaled(numeric, figures, kind, claimed)
            if match is None:
                continue  # no figure in the message supports this bound: invented
            bound = int(match.value) if float(match.value).is_integer() else match.value
        rebuilt[match.side or side] = bound

    if rebuilt:
        return rebuilt
    # Nothing matched. Either the message assigned every bound elsewhere, and the field is
    # unanswered — or it said nothing this can parse ("half a million") and the model's
    # own answer stands.
    return None if ruled_out else value


def unevidenced_range_keys(extracted: dict[str, Any], user_input: str) -> set[str]:
    """Range keys holding a bound no figure in the message supports.

    Run *after* ``correct_bound_direction``, which drops the bounds it can disprove and
    resizes the ones it can place. What is left over is the third state: values it could
    neither confirm nor rule out, because the message states a figure this cannot parse
    ("half a million"), or two figures it cannot choose between, or no figures at all.

    The model's answer is kept — it is right often enough to be worth keeping — but it is
    not an *answer* in the sense the questionnaire means. Measured across 21 recorded eval
    runs, a range value this reports is correct 32% of the time against 92% for one the
    message evidences, which is the whole reason for telling the two apart.

    The acceptance test mirrors the first branch of ``_correct_one``: same figure, same
    unit. The two have to agree, or a value that survived correction would be reported
    unevidenced and asked about for no reason.
    """
    figures = numbers_with_direction(user_input)
    unevidenced: set[str] = set()
    for key, value in extracted.items():
        if not isinstance(value, dict):
            continue
        stated = [value[side] for side in ("min", "max") if value.get(side) is not None]
        if not stated:
            continue
        kind = _FIELD_KINDS.get(key)
        for bound in stated:
            try:
                numeric = float(bound)
            except (TypeError, ValueError):
                unevidenced.add(key)
                break
            if not any(f.value == numeric and _fits(f, kind) for f in figures):
                unevidenced.add(key)
                break
    return unevidenced


def correct_bound_direction(extracted: dict[str, Any], user_input: str) -> dict[str, Any]:
    """Put each range bound on the side, and in the field, its own figure indicates.

    Three failures, one cause. The model puts a stated bound on the wrong side ("lower
    than $2M" → ``{"min": 2000000}``), it invents the opposite bound to fill the shape
    ("less than $1M" → ``{"min": 0, "max": 1000000}``), and it reuses one figure for a
    second field the message never mentioned ("100k sqft" → a budget of 100000 as well as
    a size). All three are settled by asking which figure in the message each bound came
    from, and what that figure measures.

    A bound whose value appears nowhere in the message was not stated, so it is dropped.
    A bound matching a figure measured in another field's unit belongs to that other
    field, so it is dropped and the key with it. A bound whose figure carries a comparator
    moves to that side. If no bound matches any figure the value is returned untouched, so
    an unparseable figure costs coverage rather than correctness.
    """
    figures = numbers_with_direction(user_input)
    if not figures:
        return extracted

    corrected: dict[str, Any] = {}
    for key, value in extracted.items():
        if not isinstance(value, dict):
            corrected[key] = value
            continue
        rebuilt = _correct_one(value, figures, _FIELD_KINDS.get(key))
        if rebuilt is not None:
            corrected[key] = rebuilt
    return corrected
