"""Gold and text for one field at a time, always as a pair.

Every function here returns ``(gold, wording)`` together, and that pairing is the whole
correctness argument of the generator: the criteria dict is chosen first and the sentence is
rendered *from* it, so a label cannot disagree with the message it came from. There is no
teacher to be wrong.

Two fields need more than formatting. ``_place`` resolves a nickname to the city it means,
because "SF" has to gold as San Francisco while "Tampa" must never gold as "Tampa, FL" --
normalising is not the same as inventing. ``_type_words`` renders a phrasing rather than the
option word itself, since a set where the message always contains the gold word teaches
copying, which is exactly what the tuned model did with "warehouse".
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from pipeline.data.figures import (
    PRICE_NUMBERS,
    SQFT_NUMBERS,
    _fmt_money,
    _fmt_sqft_solo,
    _price_value,
    _range_phrase,
    _sqft_value,
)
from pipeline.data.vocabulary import (
    _AMBIGUOUS_WEIGHT,
    AMBIGUOUS_TYPE_PHRASINGS,
    CITIES,
    CITY_ALIASES,
    FIELD_LABELS,
    LOCATION_TEMPLATES,
    STATES,
    TYPE_TEMPLATES,
    TYPE_TEMPLATES_ARTICLE,
)


def _article(text: str) -> str:
    """"an" before a vowel sound, near enough for generated text.

    Naive on purpose: the alternative is a pronunciation dictionary for five templates.
    """
    return "an" if text[:1].lower() in "aeiou" else "a"


def _type_templates(words: str, options: list[str]) -> list[str]:
    """Article forms only where an article reads correctly.

    "a shop" and "a warehouse" are what a client writes. "a land", "a specialty" and "a
    office or flex" are not: the option words are mass or adjectival nouns, and a
    multi-select rendering already carries its own conjunction. Restricting the article
    to a single phrasing buys the structural coverage without the ungrammatical text.
    """
    if words.lower() in options or " or " in words or "," in words:
        return TYPE_TEMPLATES
    return TYPE_TEMPLATES + TYPE_TEMPLATES_ARTICLE


def _skip_label(key: str) -> str:
    """A phrase for naming ``key`` in a refusal.

    A new required question would otherwise raise KeyError mid-generation. The fallback is
    poorer training text than a hand-written label, so add one here when that happens —
    but a plain de-underscored key is a real thing a user would type, and generating is
    better than crashing.
    """
    return random.choice(FIELD_LABELS.get(key) or [key.replace("_", " ")])


def load_phrasings(path: Path) -> dict[str, list[str]]:
    """Wordings a client uses for each option, from ``pipeline.data.make_phrasings``.

    Every property_type example used to render the option word itself, so the most
    reinforced rule in the set was *copy the noun you see* — and the tuned model echoed
    "warehouse" back instead of answering "industrial". These phrasings put a different
    word in the message from the one in the gold label, which is the only way the set can
    teach anything other than copying.

    Absent is not fatal: examples fall back to the literal option, which is the old
    behaviour.
    """
    if not path.exists():
        print(
            f"no phrasings at {path}; "
            "run pipeline.data.make_phrasings to teach generalisation"
        )
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def property_type_values(questions: list[dict[str, Any]]) -> list[str]:
    """The property types this questionnaire actually offers.

    Read from ``questions.json`` rather than hardcoded. The hardcoded list held six
    title-case types including "Warehouse" — which no listing carries and the
    questionnaire has never offered — so every generated example naming it taught a
    value the model could not legally emit.
    """
    for row in questions:
        if row.get("key") != "property_type":
            continue
        options = row.get("options")
        if not isinstance(options, list):
            break
        return [
            value
            for option in options
            if isinstance(
                value := (option.get("value") if isinstance(option, dict) else option), str
            )
            and value.strip()
        ]
    raise SystemExit(
        "questions.json has no property_type options; run pipeline.data.dump_questions"
    )


def _phrasing_weights(option: str, pool: list[str]) -> list[float]:
    ambiguous = AMBIGUOUS_TYPE_PHRASINGS.get(option, ())
    return [_AMBIGUOUS_WEIGHT if p in ambiguous else 1.0 for p in pool]


def _type_words(
    property_types: list[str], phrasings: dict[str, list[str]]
) -> tuple[list[str], str]:
    """Pick one or two types and render them as the user would name them."""
    picked = random.sample(property_types, random.choice([1, 1, 1, 2]))
    words = []
    for option in picked:
        pool = phrasings.get(option, [])
        # Half literal. All-phrasing would teach the mirror-image mistake: the model
        # would stop recognising the option words themselves.
        if pool and random.random() < 0.5:
            words.append(random.choices(pool, weights=_phrasing_weights(option, pool))[0])
        else:
            words.append(option)
    return picked, " or ".join(words)


def _place() -> tuple[str, str]:
    """Return (gold, the words the message uses).

    Four shapes, because v3 only ever produced the first two and failed on the others:

    * ``Austin`` -- bare city, gold identical
    * ``Austin, TX`` -- city and state, gold identical
    * ``SF`` -- a nickname, gold **resolved** to ``San Francisco``
    * ``California`` -- a state alone, gold identical

    The nickname is the one case where gold differs from the words, and it is the same
    normalization ``property_type`` does for "warehouse" -> industrial: a shorter name for
    the same place, not a region invented out of nothing. The "never add a region it
    omits" rule still holds -- ``Tampa`` is never labelled ``Tampa, FL``.

    Took a ``names_state`` flag that forced the first two shapes and skipped the other two.
    All three callers used the default, so the parameter's only effect was to describe a
    v3-era mode that nothing selects -- and it read as though the alias and state shapes
    were optional, which is the opposite of why they exist.
    """
    shape = random.choices(["city", "city_state", "alias", "state"],
                           weights=[30, 35, 20, 15])[0]

    if shape == "alias":
        alias, canonical = random.choice(list(CITY_ALIASES.items()))
        return canonical, alias
    if shape == "state":
        state = random.choice(STATES)
        return state, state

    city, state = random.choice(CITIES)
    if shape == "city_state":
        return f"{city}, {state}", f"{city}, {state}"
    return city, city


def _field_piece(
    key: str, property_types: list[str], phrasings: dict[str, list[str]]
) -> tuple[Any, str]:
    """Return (gold value, a bare phrase that slots into a sentence).

    The difference from ``_field_fragment`` is that a piece is not a standalone clause:
    "Miami" rather than "I'm looking in Miami", "retail" rather than "we need retail
    space". ``_connected_sentence`` weaves pieces together.
    """
    if key == "location":
        return _place()
    if key == "property_type":
        picked, words = _type_words(property_types, phrasings)
        return picked, words
    if key == "price":
        return _range_phrase(PRICE_NUMBERS)
    if key == "size_sqft":
        return _range_phrase(SQFT_NUMBERS)
    raise ValueError(f"no piece renderer for {key}; add one before regenerating")


def _bare_answer(
    key: str, property_types: list[str], phrasings: dict[str, list[str]]
) -> tuple[Any, str]:
    """A reply that is only a value -- what someone types when asked a direct question.

    For the numeric fields this is a naked figure with no unit and no currency symbol, so
    the message carries no clue which field it belongs to. That is deliberate: it is the
    turn that made "10" become a $10 budget, and only ``pending_question`` resolves it.

    Bounds split on whether a unit survives into the text. A naked figure is exact for
    size: this is the turn that made "10" a $10 budget, and v3's max-only made an answer
    of "32" a 32 sqft ceiling with every later correction stacking against it. Once a unit
    is attached the message reads the same as "130k sqft" anywhere else, so it takes the
    same ceiling gold -- otherwise one string carries two golds depending on the shape it
    landed in, which is supervision the model cannot resolve.
    """
    if key == "location":
        gold, place = _place()
        return gold, place
    if key == "property_type":
        picked, words = _type_words(property_types, phrasings)
        return picked, words
    if key == "price":
        value = _price_value()
        text = random.choice([f"{value:,}", str(value), _fmt_money(value)])
        return {"max": value}, text
    if key == "size_sqft":
        value = _sqft_value()
        if random.random() < 0.34:
            return {"max": value}, _fmt_sqft_solo(value)
        return {"min": value, "max": value}, random.choice([f"{value:,}", str(value)])
    raise ValueError(f"no bare answer for {key}; add one before regenerating")


def _field_fragment(
    key: str, property_types: list[str], phrasings: dict[str, list[str]]
) -> tuple[Any, str]:
    """Return (gold value, natural-language fragment) for one field."""
    if key == "location":
        gold, place = _place()
        return gold, random.choice(LOCATION_TEMPLATES).format(place=place)
    if key == "property_type":
        picked, words = _type_words(property_types, phrasings)
        template = random.choice(_type_templates(words, property_types))
        return picked, template.format(types=words, a=_article(words))
    if key == "price":
        bounds, phrase = _range_phrase(PRICE_NUMBERS)
        return bounds, random.choice([f"budget {phrase}", phrase, f"we can spend {phrase}"])
    if key == "size_sqft":
        bounds, phrase = _range_phrase(SQFT_NUMBERS)
        return bounds, phrase
    # Reached when the questionnaire gains a key this generator has no renderer for.
    # Raising is deliberate: silently skipping would ship a set that never teaches the
    # new field, and the shortfall would look like ordinary deduplication loss.
    raise ValueError(f"no generator for {key}; add one before regenerating")
