"""Normalize intake answers into the flat storage format search expects."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from app.domain.bounds import correct_bound_direction, unevidenced_range_keys
from app.domain.intake_vocabulary import (
    GENERIC_PHRASINGS,
    GEO_STOPWORDS,
    STATE_ABBREVIATIONS,
    TYPE_PHRASINGS,
)
from app.utils.values import clean_str_or_none

_LOCATION_TYPES = frozenset({"location", "geo", "address"})
_MULTI_SELECT_TYPES = frozenset(
    {"multiselect", "multi_select", "multi-select", "tags", "checkboxes", "building_types"},
)
_RANGE_TYPES = frozenset(
    {"range", "numeric_range", "sqft_range", "rent_range", "size_range"},
)
_SINGLE_SELECT_TYPES = frozenset({"select", "single_choice", "radio"})


def _normalize_location(value: Any) -> str | Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = [
            part
            for key in ("city", "state", "country")
            if (part := clean_str_or_none(value.get(key)))
        ]
        if parts:
            return ", ".join(parts)
        for key in ("label", "input"):
            if text := clean_str_or_none(value.get(key)):
                return text
    return value


def _normalize_multi_select(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _normalize_range(value: Any) -> dict[str, Any] | Any:
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for key in ("min", "max"):
        raw = value.get(key)
        if raw is None:
            continue
        try:
            out[key] = float(raw)
        except (TypeError, ValueError):
            continue
    unit = value.get("unit")
    if isinstance(unit, str) and unit.strip():
        out["unit"] = unit.strip()
    return out or value


def normalize_intake_value(question_type: str, value: Any) -> Any:
    """Coerce LLM or guided answers into stored criteria values."""
    qtype = question_type.strip().lower() if isinstance(question_type, str) else "text"

    if qtype in _LOCATION_TYPES:
        return _normalize_location(value)
    if qtype in _MULTI_SELECT_TYPES:
        return _normalize_multi_select(value)
    if qtype in _RANGE_TYPES:
        return _normalize_range(value)
    return value


# Stand-ins for "the user did not say". Matched exactly, never as substrings.
_PLACEHOLDER_VALUES = frozenset({
    "unknown", "unspecified", "not specified", "not provided", "not mentioned",
    "not applicable", "n/a", "n.a.", "na", "none", "null", "nil", "nan",
    "tbd", "to be determined", "any", "anything", "no preference",
    "-", "--", "?", "???",
})


def _is_placeholder(value: object) -> bool:
    return isinstance(value, str) and (
        not value.strip() or value.strip().casefold() in _PLACEHOLDER_VALUES
    )


def drop_placeholder_values(extracted: dict[str, Any]) -> dict[str, Any]:
    """Remove answers that stand in for "the user did not say".

    Asked about a field the message never mentions, the model fills the slot rather than
    omitting the key: ``location: "Unknown"`` was shown to a user as their chosen
    location, and counted as answered so the question was never asked. A filler is not an
    answer — dropping the key leaves the field missing.

    Matching is exact after trimming and case folding, never a substring, so real values
    that merely contain one of these words ("Unknown Street", "Nome") are untouched.
    An all-null range (``{"min": null, "max": null}``) is treated the same way.
    """
    cleaned: dict[str, Any] = {}
    for key, value in extracted.items():
        if _is_placeholder(value):
            continue
        if isinstance(value, list):
            if kept := [item for item in value if not _is_placeholder(item)]:
                cleaned[key] = kept
            continue
        if isinstance(value, dict):
            if any(inner is not None for inner in value.values()):
                cleaned[key] = value
            continue
        cleaned[key] = value
    return cleaned


# Generic structure nouns. A place is never bare "Building" — that is the model naming
# what the user is shopping for, in the slot for where they want it.
_GENERIC_PLACE_NOUNS = frozenset({
    "building", "buildings", "property", "properties", "space", "spaces",
    "house", "home", "site", "unit", "premises", "real estate",
    "commercial property", "commercial space", "commercial real estate",
})
# Trailing words stripped before comparing a location against the property types, so
# "industrial space" is recognised as the property type it is.
_PLACE_NOUN_SUFFIXES = (" space", " property", " building", " premises", " unit", " site")


def _self_describing_aliases(row: dict[str, Any]) -> set[str]:
    """Casefolded ways of naming the question itself, rather than answering it."""
    names = {row.get("key"), row.get("title"), row.get("label")}
    folded = {name.strip().casefold() for name in names if isinstance(name, str) and name.strip()}
    key = row.get("key")
    if isinstance(key, str):
        folded.add(key.replace("_", " ").strip().casefold())
    return folded


def drop_self_describing_values(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Remove answers that describe the field instead of answering it.

    With nothing in the message to put in a slot, the model reaches for the nearest
    noun. ``location`` came back as ``"Building"`` for "I am finding a building…", as
    ``"Location"`` (the field's own label), and as ``"industrial space"`` — the property
    type, in the slot for where the property should be.

    Three rules, all exact matches after trimming and case folding:

    * any field: the value names the question (its key, title or label);
    * a location: the value is a bare structure noun;
    * a location: the value is one of the configured property types, with a trailing
      generic noun ignored so "industrial space" is caught alongside "industrial".

    Matching is never substring, so "Building Heights" and "Property Lane, Dallas"
    survive. Bare "commercial" is deliberately not listed: unlike the others it is a
    plausible place name, and a lone word that might be a real location is worth keeping
    over catching one more echo.
    """
    rows_by_key = {row["key"]: row for row in questions if isinstance(row.get("key"), str)}
    choice_names = {
        alias
        for row in questions
        for alias in _choice_aliases(row)
    } | {
        canonical.casefold()
        for row in questions
        for canonical in _choice_aliases(row).values()
    }

    cleaned: dict[str, Any] = {}
    for key, value in extracted.items():
        row = rows_by_key.get(key)
        if row is None or not isinstance(value, str) or not value.strip():
            cleaned[key] = value
            continue

        folded = value.strip().casefold()
        if folded in _self_describing_aliases(row):
            continue

        qtype = row.get("type")
        qtype = qtype.strip().lower() if isinstance(qtype, str) else "text"
        if qtype in _LOCATION_TYPES:
            if folded in _GENERIC_PLACE_NOUNS:
                continue
            stem = folded
            for suffix in _PLACE_NOUN_SUFFIXES:
                if stem.endswith(suffix):
                    stem = stem[: -len(suffix)].strip()
                    break
            if stem in choice_names:
                continue

        cleaned[key] = value
    return cleaned


_RANGE_KEYS = frozenset({"min", "max", "unit"})


def _is_range(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and set(value) <= _RANGE_KEYS


def _numeric(value: Any) -> float | None:
    """The value as a number, or None when it is not one.

    Bounds are merged before ``normalize_merged_criteria`` coerces them, so a bound here
    can still be a string or None straight from the model. Comparing those would raise.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _merge_range(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    """Fold one turn's bounds into a stored range, dropping a bound it contradicts.

    Bound-wise merging is what lets "under $1M" then "more than 100K" keep both. The same
    rule turns a *correction* into nonsense: after "up to 32 sqft", the reply "more than
    100" leaves the ceiling in place and stores ``min 100, max 32``. That range matches no
    listing, and nothing downstream rejects it — it reaches the SQL filter intact.

    When the bounds contradict, the one this turn stated wins and the carried-forward one
    is dropped. Saying "more than 100" after "up to 32" cannot mean both; the ceiling is
    what the user is replacing.

    Equality counts as contradiction here, because a lone bound is phrased "more than 32"
    or "at least 32" — after a stored ceiling of 32 that would collapse to *exactly* 32,
    the one reading the words rule out. An exact size is still storable: it arrives as both
    bounds in the same turn, which this never touches.

    A turn that states both bounds inverted is also left as it came. Nothing was carried
    forward, so there is no stale bound to identify, and guessing which end the user meant
    would be inventing an answer.
    """
    merged = {**existing, **incoming}
    low, high = _numeric(merged.get("min")), _numeric(merged.get("max"))
    if low is None or high is None:
        return merged

    if "min" in incoming and "max" not in incoming and high <= low:
        return {key: value for key, value in merged.items() if key != "max"}
    if "max" in incoming and "min" not in incoming and low >= high:
        return {key: value for key, value in merged.items() if key != "min"}
    return merged


def merge_criteria(current: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    """Fold this turn's answers into what the session already knows.

    A plain ``{**current, **extracted}`` replaces a range wholesale, so a turn that states
    only the other bound destroys the one already recorded: "under $1M" followed by "more
    than 100K" ends up as ``{"min": 100000}`` with the ceiling gone. The user stated two
    bounds and the session keeps one.

    Ranges therefore merge bound-wise, this turn winning per key. Corrections still work —
    ``{"max": 1000000}`` then ``{"max": 3000000}`` gives ``{"max": 3000000}`` — because
    only the bounds actually restated are overwritten. Every other type replaces, which is
    what a corrected location or property type should do.

    A bound is only removed when this turn's bound contradicts it; see ``_merge_range``.
    Short of that, dropping one is far rarer than adding the second, and silently losing a
    stated bound is the worse failure.
    """
    merged = dict(current)
    for key, value in extracted.items():
        existing = merged.get(key)
        merged[key] = (
            _merge_range(existing, value)
            if _is_range(existing) and _is_range(value)
            else value
        )
    return merged


def _choice_aliases(row: dict[str, Any]) -> dict[str, str]:
    """Map every accepted spelling (casefolded) to the value that should be stored.

    Question rows come in two shapes and both occur in this codebase:
    ``intake-parser/datasets/questions.json`` uses plain strings
    (``["Office", "Retail"]``) while the database uses
    ``[{"label": "Industrial", "value": "industrial"}]``. Reading only the string form made
    this filter a silent no-op against real data — every DB option is a dict, so nothing
    was ever recognised and every value passed through.

    Label and value are both accepted spellings; ``value`` is what gets stored. Search
    compares ``property_type`` with ``ilike``, so the choice of canonical casing does not
    affect matching.

    Range questions carry ``options`` as a dict (``{"unit": "USD"}``), so only a list is
    an enumeration.
    """
    options = row.get("options")
    if not isinstance(options, list):
        return {}

    aliases: dict[str, str] = {}
    for choice in options:
        if isinstance(choice, str) and choice.strip():
            aliases[choice.strip().casefold()] = choice.strip()
            continue
        if not isinstance(choice, dict):
            continue
        spellings = [
            text.strip()
            for key in ("value", "label")
            if isinstance(text := choice.get(key), str) and text.strip()
        ]
        if not spellings:
            continue
        for spelling in spellings:
            aliases[spelling.casefold()] = spellings[0]
    return aliases


def _canonical_choice(value: str, aliases: dict[str, str]) -> str | None:
    """The stored spelling of ``value``, or None when it is not a configured choice."""
    return aliases.get(value.strip().casefold())


def _dedupe(values: Iterable[str]) -> list[str]:
    """First occurrence wins, order preserved.

    ``warehouse, restaurant, shop`` came back from production as
    ``["industrial", "retail", "retail"]``: three phrasings, two of them the same type.
    Canonicalisation is what creates the repeat -- distinct inputs map onto one stored
    value -- so it has to be undone here rather than upstream, and ``["Retail", "retail"]``
    collapses the same way. A repeated value widens no search and reads as a defect in the
    summary the client is shown.
    """
    return list(dict.fromkeys(values))


def _is_option_dump(chosen: list[str], aliases: dict[str, str]) -> bool:
    """True when a multi-select answer is simply the whole option list.

    Free text never means "office, retail, industrial, warehouse, flex and land" — that
    is the model copying the schema's choices into the answer, which the prompt rules
    already forbid and the stock model does constantly. Two-choice questions are excluded
    because "buy or lease" genuinely can be both.
    """
    configured = set(aliases.values())
    return len(configured) > 2 and set(chosen) == configured


def drop_unconfigured_choices(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Remove select / multi-select answers that are not offered by the questionnaire.

    The intake service filters extracted keys against ``question_keys`` but never checks
    values, so ``property_type: ["house"]`` — a type this questionnaire does not offer —
    is stored, counted as answered, and handed to the SQL filter. Dropping the key
    instead leaves the field missing, so it gets asked again.

    Values differing only in case are kept and canonicalised to the configured spelling.
    """
    rows_by_key = {row["key"]: row for row in questions if isinstance(row.get("key"), str)}

    cleaned: dict[str, Any] = {}
    for key, value in extracted.items():
        row = rows_by_key.get(key)
        if row is None:
            cleaned[key] = value
            continue

        qtype = row.get("type")
        qtype = qtype.strip().lower() if isinstance(qtype, str) else "text"
        aliases = _choice_aliases(row)
        if not aliases or qtype not in (_MULTI_SELECT_TYPES | _SINGLE_SELECT_TYPES):
            cleaned[key] = value
            continue

        if qtype in _MULTI_SELECT_TYPES:
            chosen = _dedupe(
                canonical
                for item in _normalize_multi_select(value)
                if (canonical := _canonical_choice(item, aliases)) is not None
            )
            if chosen and not _is_option_dump(chosen, aliases):
                cleaned[key] = chosen
            continue

        if isinstance(value, str) and (canonical := _canonical_choice(value, aliases)):
            cleaned[key] = canonical

    return cleaned


_WORD_CHARS = re.compile(r"[^\w\s]+")


def _folded(text: str) -> str:
    """Case, punctuation and spacing removed, so "St. Louis" and "St Louis" compare."""
    return " ".join(_WORD_CHARS.sub(" ", text).casefold().split())


def _says(phrase: str, message: str) -> bool:
    """Whether ``message`` (already folded) contains ``phrase``, also folded, as words."""
    if not phrase:
        return False
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", message) is not None


# Both sides of every comparison are folded, and the tables are folded once here rather
# than per call. Skipping this silently broke the hyphenated wordings — "high-rise
# residence" cannot match a message whose punctuation has been stripped to "high rise
# residence", so a correct multifamily was dropped whenever some other type was named.
_FOLDED_TYPE_PHRASINGS: dict[str, tuple[str, ...]] = {
    option: tuple(_folded(phrasing) for phrasing in phrasings)
    for option, phrasings in TYPE_PHRASINGS.items()
}
_FOLDED_GENERIC_PHRASINGS = frozenset(_folded(phrasing) for phrasing in GENERIC_PHRASINGS)


def _location_evidence(value: str, message: str) -> bool:
    """Whether the message names the place the answer claims.

    A location is copied out of the message, not reasoned to, so the words should still be
    there. Four ways of being there, from strictest down: the whole comma-part ("Austin"
    out of "Austin, Texas"), a postal abbreviation of it ("TX" for "Texas"), the initials
    of a multi-word part ("SF" for "San Francisco"), or any one distinctive word of it.

    Any *one* part suffices, because expanding what the user gave is the model doing its
    job — "Austin" answered as "Austin, Texas" is right, and only "Austin" is in the text.
    """
    for part in (p.strip() for p in value.split(",")):
        folded = _folded(part)
        if not folded:
            continue
        if _says(folded, message):
            return True
        if abbreviation := STATE_ABBREVIATIONS.get(folded):
            if _says(abbreviation, message):
                return True
        if folded in STATE_ABBREVIATIONS.values():
            if any(_says(name, message)
                   for name, code in STATE_ABBREVIATIONS.items() if code == folded):
                return True
        words = folded.split()
        if len(words) > 1 and _says("".join(word[0] for word in words), message):
            return True
        if any(_says(word, message)
               for word in words if len(word) > 2 and word not in GEO_STOPWORDS):
            return True
    return False


def _type_support(message: str) -> tuple[set[str], bool]:
    """Types the message names, and whether it names any type at all.

    The second half is what keeps this honest. "a depot for our trucks" is industrial and
    "a boutique on the high street" is retail, and neither word is in any table we have —
    the model reaches those by generalising, which is the entire reason it is there. So
    when the message speaks no type vocabulary the answer is left alone: silence about the
    vocabulary is not evidence against the type.

    Generic phrasings support a type without triggering the check; see
    ``GENERIC_PHRASINGS``.
    """
    supported = {
        option for option, phrasings in _FOLDED_TYPE_PHRASINGS.items()
        if _says(option, message) or any(_says(p, message) for p in phrasings)
    }
    named = any(
        _says(option, message)
        or any(_says(p, message) for p in phrasings if p not in _FOLDED_GENERIC_PHRASINGS)
        for option, phrasings in _FOLDED_TYPE_PHRASINGS.items()
    )
    return supported, named


def drop_unevidenced_values(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
    user_input: str,
    current_criteria: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The answers that survive :func:`check_evidence`; see there for the rules."""
    return check_evidence(extracted, questions, user_input, current_criteria)[0]


def values_without_evidence(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
    user_input: str,
    current_criteria: dict[str, Any] | None = None,
) -> set[str]:
    """The keys :func:`check_evidence` kept without being able to confirm them.

    Only ``property_type`` reaches this state, and only when the message names no type at
    all. Measured across 21 recorded eval runs such a value is correct 23% of the time,
    against 88% for one the message names — so it is worth storing and not worth treating
    as an answer.
    """
    return check_evidence(extracted, questions, user_input, current_criteria)[1]


def check_evidence(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
    user_input: str,
    current_criteria: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], set[str]]:
    """Sort answers into supported, unsupported and kept-but-unconfirmed.

    Returns the answers worth keeping and, separately, the keys among them the message
    could not confirm. One function rather than two so the verdict and the reason cannot
    drift apart.

    The three filters above validate against the *schema* — is this a placeholder, is it
    describing the field, is it a configured option? None of them reads the message, so a
    perfectly valid option word invented from nothing passes all three. Measured in
    production, three runs of three: "at least 20 dock doors" came back as
    ``property_type: ["industrial"]``, which is a configured choice, is not a placeholder,
    and does not name its own field. The user was then never asked which type they wanted.

    The invariant is the one ``bounds`` enforces for numbers::

        FINAL_VALUE(field) requires EVIDENCE(field, user_message)

    What counts as evidence differs by field, and the two here are not alike:

    * a **location** is copied, so its words should be in the message;
    * a **property type** is *interpreted* — "a depot for our trucks" is industrial —
      so a missing word proves nothing. The check only fires when the message names some
      type, and then removes the types it does not name. That catches the answer carrying
      a second type nobody asked for while leaving every generalisation intact.

    A value already in ``current_criteria`` is never dropped, and never reported
    unconfirmed: an earlier turn is evidence too, a multi-select replaces wholesale on
    merge — so removing a carried-forward type from "Add flex to that as well" would
    delete the type the session already held — and a field is only worth asking about
    once. That exemption is what stops the same unconfirmable answer being questioned on
    every turn of a session.
    """
    message = _folded(user_input or "")
    if not message:
        return extracted, set()

    carried = current_criteria or {}
    rows_by_key = {row["key"]: row for row in questions if isinstance(row.get("key"), str)}
    supported_types, names_a_type = _type_support(message)

    cleaned: dict[str, Any] = {}
    unconfirmed: set[str] = set()
    for key, value in extracted.items():
        row = rows_by_key.get(key)
        if row is None:
            cleaned[key] = value
            continue

        qtype = row.get("type")
        qtype = qtype.strip().lower() if isinstance(qtype, str) else "text"
        held = carried.get(key)

        if qtype in _LOCATION_TYPES and isinstance(value, str) and value.strip():
            if value.strip() == (held.strip() if isinstance(held, str) else None):
                cleaned[key] = value
            elif _location_evidence(value, message):
                cleaned[key] = value
            continue

        if qtype in _MULTI_SELECT_TYPES and _is_type_question(row):
            already = {item.casefold() for item in _normalize_multi_select(held)}
            if not names_a_type:
                # The message speaks no type vocabulary, so this is a reading of it we
                # cannot check either way — kept, but not counted as an answer.
                cleaned[key] = value
                if not already:
                    unconfirmed.add(key)
                continue
            kept = [
                item for item in _normalize_multi_select(value)
                if item.casefold() in supported_types or item.casefold() in already
            ]
            if kept:
                cleaned[key] = kept
            continue

        cleaned[key] = value
    return cleaned, unconfirmed


def _is_type_question(row: dict[str, Any]) -> bool:
    """Whether this question's choices are the property types ``TYPE_PHRASINGS`` describes.

    Matched on the configured values rather than the key name, so a questionnaire offering
    something else — building class, tenure — simply does not get the check instead of
    being measured against a vocabulary that says nothing about it.
    """
    configured = {value.casefold() for value in _choice_aliases(row).values()}
    return bool(configured) and configured <= set(TYPE_PHRASINGS)


def apply_criteria_filters(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
    user_input: str,
    current_criteria: dict[str, Any] | None = None,
    allowed_keys: set[str] | None = None,
) -> tuple[dict[str, Any], set[str]]:
    """Everything between what the model answered and what the session stores.

    Keys are filtered first, then values, then evidence, then bound direction — the order
    matters. A filler value or a choice the questionnaire does not offer has to leave the
    field *missing* rather than answered, or the session completes on something search
    cannot use and the question is never asked.

    This exists as one function so the eval harness can score what production returns
    rather than what the model emitted. Those two answers were the same thing until the
    evidence checks landed; now the model can say ``price {"min": 100000}`` for "100k
    sqft" and the user never sees it, and a number measuring only the model has stopped
    describing the product. Two copies of this chain would drift apart on the first fix
    that only one of them got.

    Returns the criteria and the keys among them the message could not confirm — stored,
    but not answers. See :func:`check_evidence`.
    """
    current = current_criteria or {}
    if allowed_keys is not None:
        extracted = {key: value for key, value in extracted.items() if key in allowed_keys}
    extracted = drop_placeholder_values(extracted)
    extracted = drop_self_describing_values(extracted, questions)
    extracted = drop_unconfigured_choices(extracted, questions)
    extracted, unconfirmed = check_evidence(extracted, questions, user_input, current)
    # The model reads the figure reliably and the comparator unreliably, so the side a
    # lone bound sits on is decided from the message itself.
    extracted = correct_bound_direction(extracted, user_input)
    # Only this turn's readings can be unconfirmed. One the session already carries was
    # asked about when it arrived, and asking again every turn is how a user who keeps
    # saying "around a million" is never allowed to finish.
    unconfirmed |= unevidenced_range_keys(extracted, user_input) - set(current)
    return extracted, unconfirmed


def normalize_merged_criteria(
    merged_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
    *,
    reserved_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Normalize every answered question key in ``merged_criteria``."""
    reserved = reserved_keys or frozenset()
    type_by_key = {
        row["key"]: row["type"]
        for row in questions
        if isinstance(row.get("key"), str) and isinstance(row.get("type"), str)
    }
    normalized: dict[str, Any] = {}
    for key, value in merged_criteria.items():
        if key in reserved:
            normalized[key] = value
            continue
        normalized[key] = normalize_intake_value(type_by_key.get(key, "text"), value)
    return normalized
