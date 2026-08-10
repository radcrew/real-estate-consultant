"""Generate programmatically-labelled intake training examples.

    cd backend
    python -m ml.data.generate --count 2000 --out ml/data/train.jsonl

Labels are correct by construction: a target criteria dict is chosen first, then rendered
into natural language, and the dict is kept as gold. Nothing is inferred from model output,
so there is no teacher to be wrong.

**What this set has to teach is precision, not recall.** The P2 baseline
(``ml/eval/results.md``) put the stock 0.5B at precision 0.15 with recall 1.0: it returns
every schema property on every turn, nulls included, and lists the same key in ``extracted``
and ``skipped_fields`` at once. So the generator is built around negative space —

- most examples state one or two fields and their gold names one or two, absent not null;
- a fixed share have gold ``extracted == {}`` (empty input, greetings, off-topic, pure
  skips), because "say nothing" is the behaviour most missing from the stock model;
- no example ever lists a key in both ``extracted`` and ``skipped_fields``.

Prompts are built by ``build_intake_messages``, the same function production calls, so the
training text cannot drift from what the model will see at serving time.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from pydantic import ValidationError

from app.llm.intake.service import build_intake_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput
from ml.paths import EVAL_DATASET_PATH, PHRASINGS_PATH, QUESTIONS_PATH, TRAIN_PATH, VAL_PATH

# Drawn from backend/dataset/raw-data.json so the distribution matches real listings.
CITIES = [
    ("Austin", "TX"), ("Dallas", "TX"), ("Houston", "TX"), ("Denver", "CO"),
    ("Phoenix", "AZ"), ("Miami", "FL"), ("Seattle", "WA"), ("Chicago", "IL"),
    ("Atlanta", "GA"), ("Portland", "OR"), ("Nashville", "TN"), ("Charlotte", "NC"),
    ("Wailuku", "HI"), ("Boise", "ID"), ("Reno", "NV"), ("Tampa", "FL"),
    ("San Francisco", "CA"), ("Los Angeles", "CA"), ("San Diego", "CA"),
    ("Sacramento", "CA"), ("Las Vegas", "NV"), ("Salt Lake City", "UT"),
    ("Kansas City", "MO"), ("St. Louis", "MO"), ("Columbus", "OH"),
    ("Indianapolis", "IN"), ("Raleigh", "NC"), ("Orlando", "FL"),
    ("Jacksonville", "FL"), ("San Antonio", "TX"), ("Fort Worth", "TX"),
    ("Oklahoma City", "OK"), ("Memphis", "TN"), ("Louisville", "KY"),
    ("Milwaukee", "WI"), ("Minneapolis", "MN"), ("Pittsburgh", "PA"),
    ("Philadelphia", "PA"), ("Baltimore", "MD"), ("Richmond", "VA"),
    ("Albuquerque", "NM"), ("Tucson", "AZ"), ("Omaha", "NE"), ("Tulsa", "OK"),
]

# How clients actually type a city, mapped to the name that goes in gold. Unlike the
# "never add a region it omits" rule -- which stops "Tampa" being labelled "Tampa, FL" --
# these are the *same* place under a shorter name, so normalizing is not inventing.
#
# "located in SF" returned nothing at all: no message in the v3 set contained a nickname,
# so the model had never been shown that one resolves to a city.
CITY_ALIASES = {
    "SF": "San Francisco", "San Fran": "San Francisco", "the Bay Area": "San Francisco",
    "LA": "Los Angeles", "L.A.": "Los Angeles",
    "NYC": "New York", "New York City": "New York", "Manhattan": "New York",
    "Vegas": "Las Vegas", "Philly": "Philadelphia", "ATX": "Austin",
    "DFW": "Dallas", "H-town": "Houston", "SLC": "Salt Lake City",
    "KC": "Kansas City", "OKC": "Oklahoma City", "NOLA": "New Orleans",
    "PDX": "Portland", "ABQ": "Albuquerque", "the Twin Cities": "Minneapolis",
    "SoCal": "Los Angeles", "the Valley": "Phoenix",
}

# A state on its own is a legitimate answer -- "shopping mall in California" -- and the v3
# set never produced one, so every location it saw was a city. Gold is the state as
# written; there is no city to resolve it to.
STATES = [
    "California", "Texas", "Florida", "Colorado", "Arizona", "Washington",
    "Oregon", "Nevada", "Georgia", "Tennessee", "North Carolina", "South Carolina",
    "Illinois", "Ohio", "Michigan", "Pennsylvania", "New York", "New Jersey",
    "Massachusetts", "Virginia", "Maryland", "Missouri", "Minnesota", "Utah",
    "Idaho", "Oklahoma", "Kansas", "Indiana", "Wisconsin", "Kentucky",
]

# Standalone location clauses. ``_place`` decides what the place is called and what gold
# it carries, so these only wrap it -- otherwise a template naming {city}, {state} could
# not express "SF" or "California" at all.
LOCATION_TEMPLATES = [
    "I'm looking in {place}", "we need something in {place}", "{place}",
    "somewhere around {place}", "{place} area please", "looking at {place}",
    "located in {place}", "in {place}", "{place} market", "around {place}",
]
TYPE_TEMPLATES = [
    "we need {types} space", "{types} please", "looking for {types}",
    "something {types}", "{types} would work",
]
# A refusal and a piece of noise both produce empty ``extracted``; the only signal
# separating them is phrasing. The first pass used 14 refusal strings and the model
# learned the strings, not the concept - it answered four of ten eval refusals by
# re-asking the very field being refused. Breadth here is the fix, so these are
# deliberately long and varied in register.
SKIP_PHRASES = [
    "skip", "skip it", "skip this", "skip that one", "skip this one", "just skip it",
    "pass", "pass on that", "I'll pass", "next", "next question", "next one please",
    "move on", "let's move on", "move on please", "can we move on", "moving on",
    "no preference", "no strong preference", "no strong feelings there", "no opinion",
    "doesn't matter", "does not matter", "doesn't really matter", "it doesn't matter to me",
    "I don't care", "don't care", "I really don't mind", "I don't mind", "not fussed",
    "not important", "that's not important", "not important right now", "unimportant",
    "whatever works", "anything works", "any is fine", "either is fine", "open to anything",
    "I'd rather not say", "prefer not to answer", "rather not answer that",
    "I don't want to answer that", "not answering that", "leave that one",
    "leave it blank", "leave that empty", "no answer", "n/a", "not applicable",
    "flexible on that", "we're flexible there", "we're open on that", "undecided",
    "haven't decided", "not sure yet", "no idea yet", "TBD", "come back to that",
    "ask me later", "later", "I'll figure that out later", "no requirement there",
]
NOISE_INPUTS = [
    "", "   ", "\n", "hi", "hello there", "hey", "hey there", "good morning",
    "what can you help me with?", "how does this work?", "what do you need from me?",
    "who are you?", "are you a bot?", "can you explain?", "what happens next?",
    "asdkjfh", "???", "...", "test", "aaa", "qwerty",
    "thanks", "thank you", "ok", "okay", "alright", "sounds good", "got it",
    "cool", "nice", "sure", "yes", "yep", "yeah", "no worries", "perfect",
    "that's everything", "nothing else", "that's all", "done", "all set",
]

# Confirmations that add no new criteria. Deliberately longer than the four this used to
# hold: ``eval_input_keys`` now excludes any wording the eval scores on, and three of the
# original four were eval turns, which would have collapsed this shape to one string.
COMPLETE_PHRASES = [
    "that's everything", "yes that's correct", "sounds good", "looks right",
    "that covers it", "that's the lot", "correct, that's all of it",
    "yep, we're good", "no changes needed", "confirmed", "that all looks right",
]

# Requirements the questionnaire does not ask about. They belong in no field, so gold
# ignores them entirely -- which is the behaviour being taught.
#
# "costs more than 100K, located in SF, 3 floor, industrial property! need to have good
# view!" states two of these. v3 had seen almost none, and a model trained only on
# messages where every clause maps to a field has no example of leaving one out. Several
# carry numbers on purpose ("3 floors", "12 ft ceilings"), because the live failure is a
# stray figure being read as size or price.
DISTRACTORS = [
    "3 floors", "two storeys", "single storey", "ground floor only", "top floor",
    "need a good view", "good natural light", "corner lot", "street frontage",
    "must have parking", "parking for 20 cars", "close to the highway",
    "near public transport", "walking distance to downtown",
    "12 ft ceilings", "high ceilings", "a loading dock would help",
    "three phase power", "air conditioned", "newly renovated", "move-in ready",
    "somewhere quiet", "no basement", "fenced yard", "24/7 access",
    "pet friendly", "wheelchair accessible", "fibre internet",
    "we'd like it modern", "nothing too old", "something with character",
]

# Labels a user would plausibly use when naming a field they want to skip. Keyed by the
# questionnaire's required fields; ``_skip_label`` falls back for any key added later.
FIELD_LABELS = {
    "location": ["location", "city", "area"],
    "property_type": ["property type", "space type", "building type"],
    "price": ["budget", "price", "price range"],
    "size_sqft": ["size", "square footage", "size question"],
}


def _skip_label(key: str) -> str:
    """A phrase for naming ``key`` in a refusal.

    A new required question would otherwise raise KeyError mid-generation. The fallback is
    poorer training text than a hand-written label, so add one here when that happens —
    but a plain de-underscored key is a real thing a user would type, and generating is
    better than crashing.
    """
    return random.choice(FIELD_LABELS.get(key) or [key.replace("_", " ")])


def _in_millions(value: int) -> str:
    """"$2.5M" / "2.5M" / "$2.5 million" -- including below a million: "$0.5M"."""
    millions = value / 1_000_000
    return random.choice([
        f"${millions:g}M", f"{millions:g}M", f"${millions:g}m",
        f"${millions:g} million", f"{millions:g} million", f"{millions:g} mil",
    ])


def _in_thousands(value: int) -> str:
    """"$500k" / "500K" / "500 grand" / "500k bucks".

    v3 wrote only "${n}k": always a dollar sign, always lowercase. So "costs more than
    100K" and "less than 10K bucks" -- both real messages -- arrived in a form the model
    had never seen, and it read neither as a budget.
    """
    thousands = value // 1000
    return random.choice([
        f"${thousands}k", f"${thousands}K", f"{thousands}k", f"{thousands}K",
        f"${thousands}k", f"{thousands} grand", f"{thousands}k bucks",
        f"${thousands},000", f"{thousands} thousand",
    ])


# Figures written out rather than digitised. The eval has scored "half a million", "a
# quarter of a million" and "one and a half million tops" since r1, and the generator has
# never produced one -- those turns tested a wording training never taught.
MONEY_IN_WORDS = {
    250_000: ["a quarter of a million", "quarter of a million", "250 thousand"],
    500_000: ["half a million", "a half million", "500 thousand"],
    750_000: ["three quarters of a million", "750 thousand"],
    1_000_000: ["a million", "one million", "1 mil"],
    1_500_000: ["one and a half million", "a million and a half", "1.5 mil"],
    2_000_000: ["two million", "a couple million", "2 mil"],
    3_000_000: ["three million", "3 mil"],
    5_000_000: ["five million", "5 mil"],
}
SQFT_IN_WORDS = {
    5_000: ["five thousand square feet"],
    10_000: ["ten thousand square feet"],
    20_000: ["twenty thousand square feet"],
    50_000: ["fifty thousand square feet"],
}

# "about 5,000 sqft" is still a bound, not a new kind of value -- gold is unchanged. Only
# the wording softens, and v3 saw none of it.
APPROX_PREFIXES = ["around ", "about ", "roughly ", "approximately ", "~", "somewhere near "]


def _fmt_money(value: int) -> str:
    if value in MONEY_IN_WORDS and random.random() < 0.25:
        return random.choice(MONEY_IN_WORDS[value])
    if value >= 1_000_000 and value % 100_000 == 0:
        return _in_millions(value)
    # Sub-million budgets written in millions. M-notation used to start at 1,000,000, so
    # the model only ever saw a leading digit of 1 or more and broke on a leading zero
    # two ways: "$0.1M" came back as the bare token 0.1M -- invalid JSON, not merely a
    # wrong number -- and "$0.1 million" as 1000000, a factor of ten out.
    #
    # Kept a minority form, because "$500k" is still how most people write this.
    if value >= 100_000 and value % 50_000 == 0 and random.random() < 0.3:
        return _in_millions(value)
    if value >= 1000 and value % 1000 == 0:
        return random.choice([f"${value:,}", f"{value:,} dollars", _in_thousands(value)])
    return f"${value:,}"


# Every way this industry writes square feet. v3 wrote only "sqft" and "square feet", so
# "sq ft", "sq. ft." and the ubiquitous "SF" were all unseen.
#
# "SF" is deliberately included even though CITY_ALIASES maps it to San Francisco: in
# commercial real estate it means square feet far more often, and the disambiguating
# signal -- a figure immediately before it -- is exactly what training should teach. Both
# senses appear in the set so context has to do the work.
SQFT_UNITS = ["sqft", "sq ft", "sq. ft.", "SF", "square feet", "square foot",
              "sf", "sq.ft.", "square footage"]


def _fmt_sqft(value: int) -> str:
    if value in SQFT_IN_WORDS and random.random() < 0.2:
        return random.choice(SQFT_IN_WORDS[value])
    unit = random.choice(SQFT_UNITS)
    if value >= 1000 and value % 1000 == 0 and random.random() < 0.35:
        return f"{value // 1000}k {unit}"
    return f"{value:,} {unit}"


def _price_value() -> int:
    return random.choice([
        random.randrange(200_000, 5_000_000, 100_000),
        random.randrange(20_000, 200_000, 5_000),
        # Round six-figure budgets. Without this the two ranges above meet at 200k, so
        # the band a client is most likely to state in millions -- "$0.5M" -- was reachable
        # only as one of eight values, and M-notation had almost nothing to attach to.
        random.randrange(100_000, 1_000_000, 50_000),
    ])


def _sqft_value() -> int:
    return random.randrange(1_000, 60_000, 500)


# The model has to read DIRECTION off the wording, so both sides need comparable breadth.
# v2 had 4 upper phrasings against 3 lower, and a 2:1 style weighting on top, producing
# 445 upper-bound examples against 199 lower. It generalised unseen *upper* wordings fine
# ("less than", "lower than") because the prior agreed, and inverted unseen *lower* ones:
# "higher than $500K" came back as {"max": 500000}.
MAX_PHRASES = [
    "up to {v}", "no more than {v}", "under {v}", "less than {v}", "lower than {v}",
    "below {v}", "at most {v}", "not over {v}", "{v} or less", "{v} max", "maximum {v}",
]
MIN_PHRASES = [
    "at least {v}", "no less than {v}", "more than {v}", "higher than {v}", "over {v}",
    "above {v}", "starting at {v}", "north of {v}", "{v} or more", "{v} and up",
    "minimum {v}",
]
BETWEEN_PHRASES = [
    "between {lo} and {hi}", "from {lo} to {hi}", "{lo} to {hi}",
    "more than {lo} but under {hi}", "at least {lo} and no more than {hi}",
    "in the {lo} to {hi} range", "anywhere from {lo} up to {hi}",
    "{lo} minimum, {hi} maximum", "no less than {lo}, no more than {hi}",
]
# Hyphenated ranges, which is how one is usually typed. Kept apart from BETWEEN_PHRASES
# because the low side drops its unit -- "10,000-15,000 sqft", never
# "10,000 sqft-15,000 sqft", which is what a shared template produces.
HYPHEN_PHRASES = ["{lo}-{hi}", "{lo} - {hi}", "{lo}–{hi}"]


class FieldNumbers(NamedTuple):
    """How one numeric field renders and samples, and what a bare figure means for it.

    Replaces a bare ``(callable, callable)`` tuple indexed as ``fmt[0]`` / ``fmt[1]``,
    where only the first element formatted and nothing said what the second did.
    """

    render: Callable[[int], str]  # 4200 -> "4,200 sqft"
    sample: Callable[[], int]  # draw a plausible value
    bare_is_exact: bool  # see _range_phrase
    # The low side of a hyphenated range, where the unit belongs only on the high side:
    # "10,000-15,000 sqft". Money keeps its symbol, since "$500k-$1M" is how it is written.
    render_low: Callable[[int], str]


def _range_phrase(numbers: FieldNumbers) -> tuple[dict[str, int], str]:
    """Return (gold bounds, phrasing).

    Weights are set on the **gold** distribution, not the style names: ``bare`` also
    yields a ``max`` bound for price, so explicit ``max`` is damped to compensate. The
    result is roughly 40% max-only, 40% min-only, 20% two-sided — parity is the point,
    because the imbalance is what let a learned prior override an explicit comparator.
    """
    style = random.choices(["max", "min", "between", "bare"], weights=[25, 40, 20, 15])[0]

    def soften(text: str) -> str:
        """Sometimes hedge a bare figure. The bound is unchanged; only the wording is.

        Only bare figures. Prefixing one that already carries a comparator produces
        "we can spend above around 35,000 dollars", which no one writes -- the comparator
        already conveys the imprecision.
        """
        return random.choice(APPROX_PREFIXES) + text if random.random() < 0.15 else text

    if style == "max":
        value = numbers.sample()
        return {"max": value}, random.choice(MAX_PHRASES).format(v=numbers.render(value))
    if style == "min":
        value = numbers.sample()
        return {"min": value}, random.choice(MIN_PHRASES).format(v=numbers.render(value))
    if style == "bare":
        # A figure with no comparator means different things per field, and the gold
        # conventions in results.md say so: a bare *budget* is a ceiling ("half a million"
        # -> max), a bare *size* is exact ("10,000 square feet" -> min == max).
        #
        # v3 generated max-only for both, so a user answering the size question with "32"
        # got {"max": 32} -- a ceiling of 32 sqft -- and every later correction stacked
        # against it. Scored on the eval as a value-accuracy miss, in production as a
        # search that matches nothing.
        value = numbers.sample()
        bounds = {"min": value, "max": value} if numbers.bare_is_exact else {"max": value}
        return bounds, soften(numbers.render(value))
    low = numbers.sample()
    high = low + numbers.sample()
    if random.random() < 0.3:
        return {"min": low, "max": high}, random.choice(HYPHEN_PHRASES).format(
            lo=numbers.render_low(low), hi=numbers.render(high)
        )
    return {"min": low, "max": high}, random.choice(BETWEEN_PHRASES).format(
        lo=numbers.render(low), hi=numbers.render(high)
    )


PRICE_NUMBERS = FieldNumbers(
    _fmt_money, _price_value, bare_is_exact=False, render_low=_fmt_money
)
SQFT_NUMBERS = FieldNumbers(
    _fmt_sqft, _sqft_value, bare_is_exact=True, render_low=lambda v: f"{v:,}"
)


def load_phrasings(path: Path) -> dict[str, list[str]]:
    """Wordings a client uses for each option, from ``ml.data.make_phrasings``.

    Every property_type example used to render the option word itself, so the most
    reinforced rule in the set was *copy the noun you see* — and the tuned model echoed
    "warehouse" back instead of answering "industrial". These phrasings put a different
    word in the message from the one in the gold label, which is the only way the set can
    teach anything other than copying.

    Absent is not fatal: examples fall back to the literal option, which is the old
    behaviour.
    """
    if not path.exists():
        print(f"no phrasings at {path}; run ml.data.make_phrasings to teach generalisation")
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
    raise SystemExit("questions.json has no property_type options; run ml.eval.dump_questions")


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
        words.append(random.choice(pool) if pool and random.random() < 0.5 else option)
    return picked, " or ".join(words)


def _place(names_state: bool | None = None) -> tuple[str, str]:
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
    """
    if names_state is None:
        shape = random.choices(["city", "city_state", "alias", "state"],
                               weights=[30, 35, 20, 15])[0]
    else:
        shape = "city_state" if names_state else "city"

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

    Bounds follow the same convention as any bare figure: a budget is a ceiling, a size is
    exact.
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
        text = random.choice([f"{value:,}", str(value), _fmt_sqft(value)])
        return {"min": value, "max": value}, text
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
        return picked, random.choice(TYPE_TEMPLATES).format(types=words)
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


# Openers for a woven sentence. Empty is included because "retail in Miami under $3M" is
# how people actually type.
SENTENCE_OPENERS = ["", "", "looking for ", "we want to buy ", "we need ", "I need ",
                    "after ", "trying to find ", "we're after "]
# Attached to the type when it reads naturally: "office space in Seattle".
TYPE_SUFFIXES = ["", "", " space", " property"]
# How a trailing bound joins on. "that costs" only fits price.
def _add_distractors(text: str) -> str:
    """Fold in one or two requirements the questionnaire does not cover.

    Gold is untouched, so the example teaches that a clause with no field is left out
    rather than forced into the nearest one.
    """
    if not text:
        return text
    extras = random.sample(DISTRACTORS, random.choice([1, 1, 2]))
    parts = [text, *extras]
    if random.random() < 0.4:
        random.shuffle(parts)
    return ", ".join(parts)


def _rough_up(text: str) -> str:
    """Punctuation and casing a real client uses and a template never produces.

    v3 saw no exclamation marks at all and no sentence-cased messages, so wording it had
    otherwise learned arrived looking unfamiliar.
    """
    if not text:
        return text
    roll = random.random()
    if roll < 0.10:
        text = text[0].upper() + text[1:]
    elif roll < 0.14:
        text = text.upper()
    tail = random.choices(["", "", "", "!", ".", "!!", " please", " thanks"],
                          weights=[60, 10, 10, 8, 6, 2, 2, 2])[0]
    return text + tail


def _attach(part: str, *, first: bool) -> str:
    """Join a trailing bound onto the sentence.

    Only a bound that opens with a comparator word can attach without a comma, and only
    directly after the place. A bare figure there reads as noise -- "Denver, CO 45k sqft"
    -- and a second bound run on reads as one phrase: "up to 59,500 sqft lower than
    $125k". Both appeared in the first draft of this function.
    """
    if first and part[:1].isalpha():
        return random.choice([", ", ", ", " ", " "]) + part
    return ", " + part


def _connected_sentence(pieces: dict[str, str]) -> str | None:
    """Weave field pieces into one flowing sentence, or None if they do not fit.

    v3 dropped ``location`` from every multi-field message that embedded it as a
    prepositional phrase — "retail in Miami under $3M" returned type and price only, on
    four of five multi-field eval turns and in production. It is not a merge bug: with an
    empty ``current_criteria`` the key is still absent from the model's reply.

    The cause is that this generator only ever produced comma-joined standalone clauses
    ("we need retail space, I'm looking in Miami, budget up to $3M"), so a place named
    mid-sentence was close to unseen. This is the missing shape.

    Requires both a type and a place, which is exactly the failing pattern; anything else
    falls back to the comma-joined form.
    """
    if "property_type" not in pieces or "location" not in pieces:
        return None
    head = f"{random.choice(SENTENCE_OPENERS)}{pieces['property_type']}"
    head += f"{random.choice(TYPE_SUFFIXES)} in {pieces['location']}"
    # Size before price reads more naturally than the reverse ("5,000 sqft, under $2M").
    tail = [pieces[key] for key in ("size_sqft", "price") if key in pieces]
    return head + "".join(_attach(part, first=i == 0) for i, part in enumerate(tail))


def _next_question_key(
    answered: set[str], skipped: set[str], ordered_required: list[str]
) -> str | None:
    return next((k for k in ordered_required if k not in answered and k not in skipped), None)


def make_example(
    *,
    question_keys: list[str],
    required: list[str],
    ordered_required: list[str],
    property_types: list[str],
    phrasings: dict[str, list[str]],
) -> dict[str, Any]:
    """One training example. Shape is chosen first, so sparsity is controlled, not incidental."""
    # Weighted so over half the set teaches restraint rather than extraction. `skip` is
    # over-weighted against its target share because refusal phrasings collapse under
    # deduplication far harder than extraction phrasings do.
    shape = random.choices(
        ["single", "multi", "skip", "noise", "carried-skip", "complete",
         "answer-and-skip", "correction", "pending-answer"],
        # `multi` is held at 20 because ~70% of its examples state 3+ fields, and that
        # share is the location-drop fix -- adding shapes below it once pushed 3+ down to
        # 11%, back to the v3 level the fix exists to move. `skip` stays over-weighted
        # against its target share because refusal phrasings collapse under dedup far
        # harder than extraction phrasings do.
        weights=[16, 20, 23, 9, 5, 4, 6, 9, 8],
    )[0]

    prior: dict[str, Any] = {}
    skipped: list[str] = []
    # Some turns start mid-conversation, so the model must learn not to re-extract what
    # is already in current_criteria.
    #
    # Never for `multi`: a pre-filled prior shrinks `remaining`, which caps how many
    # fields the message can state. That is why v3 saw so few 3- and 4-field examples --
    # 10.8% of the set -- and learned to stop at two.
    #
    # `correction` fills its own prior below, because it needs a field that is already
    # answered -- the opposite of what `remaining` selects for.
    if shape not in ("multi", "correction", "pending-answer") and random.random() < 0.45:
        for key in random.sample(required, random.randint(1, max(1, len(required) - 2))):
            prior[key], _ = _field_fragment(key, property_types, phrasings)

    remaining = [k for k in question_keys if k not in prior]
    if not remaining:
        remaining = [random.choice(question_keys)]

    extracted: dict[str, Any] = {}
    fragments: list[str] = []

    if shape == "pending-answer":
        # Answer the outstanding question with a value and nothing else. Every other
        # required field is filled, so `pending_question` in the prompt names exactly the
        # one this message answers -- which is the only thing that disambiguates it.
        #
        # "10" is price after the budget question and size_sqft after the size question.
        # Identical message, different field, and the message itself cannot say which:
        # that is why the prompt carries pending_question and why this shape exists.
        target = random.choice(required)
        for key in required:
            if key != target:
                prior[key], _ = _field_fragment(key, property_types, phrasings)
        extracted[target], user_input = _bare_answer(target, property_types, phrasings)
    elif shape == "correction":
        # A field that is ALREADY answered, restated. Every other shape draws from
        # `remaining`, so v3 never saw gold overlap current_criteria and learned that an
        # answered field is closed. In production a user correcting a stored value got
        # their old value echoed back unchanged, turn after turn.
        #
        # Half carry an explicit marker ("actually", "make it") and half are a bare
        # restatement, because the bare form is what failed: "100sqft" after a wrong size
        # is a correction whether or not the user says so.
        for key in random.sample(required, random.randint(1, max(1, len(required) - 1))):
            prior[key], _ = _field_fragment(key, property_types, phrasings)
        target = random.choice(list(prior))
        extracted[target], fragment = _field_fragment(target, property_types, phrasings)
        if random.random() < 0.5:
            marker = random.choice([
                "actually", "actually, make it", "sorry, make that", "no,", "scratch that,",
                "change that to", "let's say", "on second thought,", "correction:",
                "I meant", "no I meant", "update that to",
            ])
            user_input = f"{marker} {fragment}"
        else:
            user_input = fragment
    elif shape == "noise":
        user_input = random.choice(NOISE_INPUTS)
    elif shape == "skip":
        target = _next_question_key(set(prior), set(), ordered_required)
        if target is None:
            target = random.choice(required)
        skipped = [target]
        user_input = random.choice(SKIP_PHRASES)
    elif shape == "answer-and-skip":
        # One message that answers one field and refuses another. The first pass had no
        # example of this, and the eval turn that needs it failed: every skip example
        # had empty `extracted`, so answering and skipping looked mutually exclusive.
        answerable = [k for k in remaining if k in required] or remaining
        answer_key = random.choice(answerable)
        extracted[answer_key], fragment = _field_fragment(answer_key, property_types, phrasings)
        candidates = [
            k for k in required if k not in prior and k != answer_key
        ]
        if candidates:
            skip_key = random.choice(candidates)
            skipped = [skip_key]
            label = _skip_label(skip_key)
            refusal = random.choice([
                f"but skip the {label}", f"but let's skip {label}",
                f"no preference on {label} though", f"{label} doesn't matter",
                f"and I'd rather not answer the {label} question",
                f"leave {label} blank", f"flexible on {label}",
            ])
            user_input = f"{fragment}, {refusal}"
        else:
            user_input = fragment
    elif shape == "carried-skip":
        carried = random.sample(required, random.randint(1, 2))
        skipped = list(carried)
        prior = {k: v for k, v in prior.items() if k not in carried}
        available = [k for k in remaining if k not in carried]
        if available:
            key = random.choice(available)
            extracted[key], fragment = _field_fragment(key, property_types, phrasings)
            fragments.append(fragment)
        user_input = ", ".join(fragments)
    elif shape == "complete":
        for key in required:
            if key not in prior:
                prior[key], _ = _field_fragment(key, property_types, phrasings)
        user_input = random.choice(COMPLETE_PHRASES)
    elif shape == "single":
        key = random.choice(remaining)
        extracted[key], fragment = _field_fragment(key, property_types, phrasings)
        user_input = fragment
    else:
        # Skewed high on purpose. A flat randint(2, 4) still leaves 3- and 4-field
        # messages rarer than 2-field ones once the other shapes are counted, and
        # under-representing them is what taught v3 to stop after two keys.
        count = min(len(remaining), random.choices([2, 3, 4], weights=[30, 40, 30])[0])
        keys = random.sample(remaining, count)
        # Most qualifying messages are woven into one sentence; the rest stay comma-joined
        # clauses. Weighted toward weaving because that is the shape v3 failed on, but not
        # all of it -- an all-sentence set would just move the blind spot, and the
        # comma-joined form is still ~14% of the set through the other shapes.
        pieces = {}
        for key in keys:
            extracted[key], pieces[key] = _field_piece(key, property_types, phrasings)
        sentence = _connected_sentence(pieces) if random.random() < 0.6 else None
        if sentence is not None:
            user_input = sentence
        else:
            # Re-render as standalone clauses; gold is re-taken because the wording, and
            # therefore what the message actually states, differs between the two forms.
            extracted = {}
            for key in keys:
                extracted[key], fragment = _field_fragment(key, property_types, phrasings)
                fragments.append(fragment)
            user_input = ", ".join(fragments)

    # Applied once, here, so every shape gets them rather than only the ones edited last.
    # `noise` is exempt: its whole job is bare greetings and typos, and appending a
    # requirement to "hi" would turn a say-nothing example into a say-something one.
    if shape != "noise":
        if extracted and random.random() < 0.22:
            user_input = _add_distractors(user_input)
        user_input = _rough_up(user_input)

    current_criteria = dict(prior)
    if skipped and shape == "carried-skip":
        current_criteria["_skipped_fields"] = list(skipped)

    answered = set(prior) | set(extracted)
    next_key = _next_question_key(answered, set(skipped), ordered_required)

    return {
        "shape": shape,
        "user_input": user_input,
        "current_criteria": current_criteria,
        "target": {
            "extracted": extracted,
            "skipped_fields": sorted(skipped),
        },
        "next_question_key": next_key,
    }



def validate(example: dict[str, Any], question_keys: set[str], required: set[str]) -> str | None:
    """Return a reason the example is unusable, or None. Runs on every row before writing."""
    target = example["target"]
    extracted = target["extracted"]
    skipped = set(target["skipped_fields"])

    for key in extracted:
        if key not in question_keys:
            return f"extracted unknown key {key}"
    for key in skipped:
        if key not in required:
            return f"skipped non-required key {key}"
    # The stock model does exactly this; never show it an example that does.
    both = set(extracted) & skipped
    if both:
        return f"key in both extracted and skipped: {sorted(both)}"
    try:
        LlmParseModelOutput.model_validate(target)
    except ValidationError as exc:
        return f"fails LlmParseModelOutput: {exc}"
    return None


def to_chat_record(
    example: dict[str, Any], questions: list[dict[str, Any]]
) -> dict[str, Any]:
    """Render one example as chat messages, using the builder production calls."""
    prompt = build_intake_messages(
        user_input=example["user_input"],
        current_criteria=example["current_criteria"],
        questions=questions,
    )
    completion = json.dumps(example["target"], ensure_ascii=True, separators=(",", ":"))
    return {
        "messages": [*prompt.messages, {"role": "assistant", "content": completion}],
        "shape": example["shape"],
    }


def eval_input_keys(path: Path) -> set[str]:
    """Wordings the eval scores on, so training never teaches one of them.

    Keyed on ``user_input`` alone, **not** the (input, criteria) pair. For skip and
    noise turns the wording *is* the whole signal, so the same phrase under different
    conversation state is still the model recognising a string it trained on. Keying on
    the pair let r2 ship with 9 of 25 skip turns reusing a ``SKIP_PHRASES`` entry, which
    made roughly a third of skip recall memorisation.

    Deduplication still keys on the pair — see ``main`` — because the same wording
    against different state is legitimate variety *within* training.
    """
    if not path.exists():
        return set()
    return {
        json.loads(line)["user_input"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2500)
    parser.add_argument("--questions", default=str(QUESTIONS_PATH))
    parser.add_argument("--eval-set", default=str(EVAL_DATASET_PATH))
    parser.add_argument("--phrasings", default=str(PHRASINGS_PATH))
    parser.add_argument("--out", default=str(TRAIN_PATH))
    parser.add_argument("--val-out", default=str(VAL_PATH))
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    random.seed(args.seed)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    question_keys = [q["key"] for q in questions]
    property_types = property_type_values(questions)
    phrasings = load_phrasings(Path(args.phrasings))
    required = [q["key"] for q in questions if q.get("required")]
    ordered_required = [
        q["key"] for q in sorted(questions, key=lambda q: q["order_index"]) if q.get("required")
    ]

    held_out = eval_input_keys(Path(args.eval_set))
    seen: set[str] = set()
    rejected: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    shapes: Counter[str] = Counter()

    attempts = 0
    while len(records) < args.count and attempts < args.count * 60:
        attempts += 1
        example = make_example(
            question_keys=question_keys,
            required=required,
            ordered_required=ordered_required,
            property_types=property_types,
            phrasings=phrasings,
        )
        reason = validate(example, set(question_keys), set(required))
        if reason:
            rejected[reason.split(":")[0]] += 1
            continue
        if example["user_input"] in held_out:
            rejected["collides with eval set"] += 1
            continue
        identity = (
            example["user_input"],
            json.dumps(example["current_criteria"], sort_keys=True),
        )
        fingerprint = json.dumps([identity, example["target"]], sort_keys=True)
        if fingerprint in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(fingerprint)
        records.append(to_chat_record(example, questions))
        shapes[example["shape"]] += 1

    if len(records) < args.count:
        print(f"only produced {len(records)} of {args.count} after {attempts} attempts")

    random.shuffle(records)
    split = int(len(records) * (1 - args.val_fraction))
    train, val = records[:split], records[split:]

    for path_str, rows in ((args.out, train), (args.val_out, val)):
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")
        print(f"wrote {len(rows):>5} -> {path}")

    empty = sum(
        1 for r in records
        if json.loads(r["messages"][-1]["content"])["extracted"] == {}
    )
    print("\nshape mix:")
    for name, count in shapes.most_common():
        print(f"  {name:<14} {count:>5}  {count / len(records):>6.1%}")
    print(f"\nexamples with empty extracted: {empty} ({empty / len(records):.1%})")
    print("This share is the point: the stock model's failure is over-emission.")
    if rejected:
        print("\nrejected:")
        for reason, count in rejected.most_common():
            print(f"  {reason:<34} {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
