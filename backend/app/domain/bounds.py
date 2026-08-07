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


def bound_sides_in(text: str) -> set[str]:
    """Return the bound directions the message states — a subset of ``{"min", "max"}``."""
    return {_GROUP_SIDE[match.lastgroup] for match in _BOUND_RE.finditer(text or "")}


def correct_bound_direction(extracted: dict[str, Any], user_input: str) -> dict[str, Any]:
    """Move a lone bound to the side the message's comparator indicates.

    Returns ``extracted`` unchanged unless the message names exactly one direction and
    the value carries exactly the opposite bound. A message naming both directions, a
    value already carrying both, and a message naming none are all left alone.
    """
    sides = bound_sides_in(user_input)
    if len(sides) != 1:
        return extracted

    want = next(iter(sides))
    other = "max" if want == "min" else "min"

    corrected = dict(extracted)
    for key, value in extracted.items():
        if not isinstance(value, dict):
            continue
        stated = {bound for bound in ("min", "max") if value.get(bound) is not None}
        if stated == {other}:
            corrected[key] = {want: value[other]}
    return corrected
