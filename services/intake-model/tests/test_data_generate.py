"""Invariants for the programmatic training-data generator.

A bug here is invisible: it produces plausible JSONL that silently teaches the model the
wrong behaviour. These tests pin the properties the P2 baseline says matter most.
"""

from __future__ import annotations

import collections
import json
import random
import re
from pathlib import Path

import pytest

from pipeline.data.generate import (
    AMBIGUOUS_TYPE_PHRASINGS,
    BETWEEN_PHRASES,
    CITIES,
    CITY_ALIASES,
    DISTRACTORS,
    FIELD_LABELS,
    MAX_PHRASES,
    MIN_PHRASES,
    PRICE_NUMBERS,
    REVERSED_BETWEEN_PHRASES,
    SQFT_NUMBERS,
    SQFT_PER_SQYD,
    SQYD_UNITS,
    STATES,
    _field_fragment,
    _fmt_money,
    _next_question_key,
    _place,
    _price_value,
    _range_phrase,
    _skip_label,
    _type_words,
    collision_key,
    eval_input_keys,
    load_phrasings,
    make_example,
    property_type_values,
    to_chat_record,
    validate,
)
from pipeline.paths import EVAL_DATASET_PATH, PHRASINGS_PATH, QUESTIONS_PATH

# Derived from the questionnaire, never restated. A hardcoded copy is what let the
# generator and the eval spend the whole branch describing six questions the database
# has never had.
_QUESTIONS = json.loads(Path(QUESTIONS_PATH).read_text(encoding="utf-8"))
QUESTION_KEYS = [q["key"] for q in _QUESTIONS]
REQUIRED = [q["key"] for q in _QUESTIONS if q.get("required")]
ORDERED_REQUIRED = [
    q["key"] for q in sorted(_QUESTIONS, key=lambda q: q["order_index"]) if q.get("required")
]
PROPERTY_TYPES = property_type_values(_QUESTIONS)
PHRASINGS = load_phrasings(PHRASINGS_PATH)


@pytest.fixture
def questions():
    return _QUESTIONS


def _examples(n: int = 400, seed: int = 3):
    random.seed(seed)
    return [
        make_example(
            question_keys=QUESTION_KEYS,
            required=REQUIRED,
            ordered_required=ORDERED_REQUIRED,
            property_types=PROPERTY_TYPES,
            phrasings=PHRASINGS,
        )
        for _ in range(n)
    ]


class TestValidate:
    def test_rejects_a_key_in_both_extracted_and_skipped(self):
        # The stock 0.5B does exactly this; no example may demonstrate it.
        example = {
            "target": {
                "extracted": {"location": "Austin"},
                "skipped_fields": ["location"],
            }
        }
        reason = validate(example, set(QUESTION_KEYS), set(REQUIRED))
        assert reason is not None
        assert "both" in reason

    def test_rejects_unknown_extracted_key(self):
        example = {
            "target": {
                "extracted": {"made_up": 1},
                "skipped_fields": [],
            }
        }
        assert "unknown key" in (validate(example, set(QUESTION_KEYS), set(REQUIRED)) or "")

    def test_rejects_skipping_a_non_required_key(self):
        """Every live question is required, so any key here is one by definition."""
        example = {
            "target": {
                "extracted": {},
                "skipped_fields": ["not_a_required_field"],
            }
        }
        assert "non-required" in (validate(example, set(QUESTION_KEYS), set(REQUIRED)) or "")

    def test_accepts_a_clean_example(self):
        example = {
            "target": {
                "extracted": {"location": "Austin"},
                "skipped_fields": ["price"],
            }
        }
        assert validate(example, set(QUESTION_KEYS), set(REQUIRED)) is None


class TestGeneratorTracksTheQuestionnaire:
    """No renderer for a field the questionnaire does not ask, and none missing either.

    ``listing_type`` and ``loading_docks`` survived here for a whole branch after r4
    dropped them -- real listing columns, never intake questions -- which is the residue
    of the six-question fiction. Dead branches are unreachable rather than wrong, so
    nothing failed; the file just went on reading as though those fields were supported.
    """

    def test_every_required_key_has_a_skip_label(self):
        for key in REQUIRED:
            assert key in FIELD_LABELS, f"{key} would fall back to a de-underscored key"

    def test_no_skip_label_for_a_field_that_is_not_asked(self):
        assert not set(FIELD_LABELS) - set(QUESTION_KEYS)

    def test_every_question_key_can_be_rendered(self):
        random.seed(5)
        for key in QUESTION_KEYS:
            gold, fragment = _field_fragment(key, PROPERTY_TYPES, PHRASINGS)
            assert gold is not None and fragment

    def test_an_unknown_key_raises_rather_than_generating_nothing(self):
        with pytest.raises(ValueError, match="no generator"):
            _field_fragment("clear_height", PROPERTY_TYPES, PHRASINGS)

    def test_the_skip_label_fallback_is_usable_text(self):
        assert _skip_label("clear_height") == "clear height"


class TestMultiFieldShape:
    """v3 dropped ``location`` from every message that named it mid-sentence.

    "retail in Miami under $3M" returned type and price only -- on four of five
    multi-field eval turns, and in production. Not a merge bug: with an empty
    current_criteria the key is still missing from the reply. The set only ever held
    comma-joined standalone clauses, and 77% of it extracted at most one field.
    """

    def test_a_real_share_of_examples_state_three_or_more_fields(self):
        examples = _examples(n=1200, seed=7)
        counts = [len(e["target"]["extracted"]) for e in examples]
        three_plus = sum(1 for c in counts if c >= 3) / len(counts)
        assert three_plus >= 0.12, f"only {three_plus:.1%} state 3+ fields; v3 had 10.8%"

    # Standalone location clauses, lowercased. `_rough_up` may upper-case a whole message,
    # so every comparison against these has to fold case.
    CLAUSE_MARKERS = ("something in", "looking in", "somewhere around", "area please",
                      "looking at", "located in", "market", "around ")

    def test_woven_sentences_are_generated(self):
        """Raw make_example output; the written set runs higher, since dedup culls the
        collapsing shapes (skip, noise) far harder than it culls extraction phrasings."""
        examples = _examples(n=1200, seed=7)
        woven = [
            e for e in examples
            if len(e["target"]["extracted"]) >= 2
            and " in " in e["user_input"].lower()
            and not any(m in e["user_input"].lower() for m in self.CLAUSE_MARKERS)
        ]
        share = len(woven) / len(examples)
        assert share >= 0.03, f"only {share:.1%} weave the shape v3 failed on"

    def test_the_comma_joined_form_is_not_displaced(self):
        """An all-sentence set would just relocate the blind spot."""
        examples = _examples(n=1200, seed=7)
        clause = [
            e for e in examples
            if any(m in e["user_input"].lower() for m in self.CLAUSE_MARKERS)
        ]
        assert len(clause) / len(examples) >= 0.10

    def test_gold_location_is_always_traceable_to_the_message(self):
        """Gold is never invented. Two legitimate forms, and nothing else:

        * the place is written out, so gold appears in the text;
        * the place is a nickname, so gold is the canonical city it resolves to.

        Case is folded because ``_rough_up`` may upper-case the whole message.
        """
        for example in _examples(n=800, seed=9):
            location = example["target"]["extracted"].get("location")
            if not isinstance(location, str):
                continue
            text = example["user_input"].lower()
            if location.lower() in text:
                continue
            resolves = [
                alias for alias, canonical in CITY_ALIASES.items()
                if canonical == location and alias.lower() in text
            ]
            assert resolves, f"gold {location!r} is in neither form of {example['user_input']!r}"

    def test_a_bound_never_runs_into_the_place_or_another_bound(self):
        """"Denver, CO 45k sqft" and "59,500 sqft lower than $125k" both shipped once.

        The state-code pattern is anchored on the comma that precedes it -- a bare
        ``[A-Z]{2} \\d`` also matches the tail of any upper-cased word, e.g. "HIGHER THAN
        20,500".
        """
        for example in _examples(n=800, seed=13):
            text = example["user_input"]
            assert not re.search(r", [A-Z]{2} \d", text), text
            assert not re.search(r"(sqft|feet) [a-z]+ than", text, re.I), text


class TestBareFigureConventions:
    """results.md: a bare budget is a ceiling, a bare size is exact.

    v3 generated max-only for both, so answering the size question with "32" trained
    ``{"max": 32}`` -- a 32 sqft ceiling -- and every later correction stacked against it.
    """

    def _bounds(self, key: str, n: int = 900):
        random.seed(21)
        return [_field_fragment(key, PROPERTY_TYPES, PHRASINGS)[0] for _ in range(n)]

    def test_a_bare_size_sets_both_bounds_equal(self):
        exact = [b for b in self._bounds("size_sqft") if b.get("min") == b.get("max")]
        assert exact, "no exact sizes generated; the convention is scored but never taught"

    def test_a_bare_budget_is_a_ceiling_never_an_exact_price(self):
        for bounds in self._bounds("price"):
            assert not (bounds.get("min") is not None and bounds["min"] == bounds.get("max"))

    def test_the_field_decides_what_bare_means(self):
        assert SQFT_NUMBERS.bare_is_exact
        assert not PRICE_NUMBERS.bare_is_exact


class TestSubMillionMillionsNotation:
    """M-notation used to start at 1,000,000, so a leading zero was never seen.

    v3 broke on it two ways, neither of them a rounding slip: "$0.1M" came back as the
    bare token ``0.1M`` -- invalid JSON, so the turn fails outright -- and "$0.1 million"
    as 1000000, a factor of ten out and silently wrong.
    """

    def _money(self, value: int, n: int = 200) -> set[str]:
        random.seed(4)
        return {_fmt_money(value) for _ in range(n)}

    @pytest.mark.parametrize("value", [100_000, 250_000, 500_000, 900_000])
    def test_a_round_sub_million_budget_can_be_written_in_millions(self, value):
        forms = self._money(value)
        assert any("M" in f or "million" in f for f in forms), f"{value}: {sorted(forms)}"

    @pytest.mark.parametrize("value", [100_000, 500_000])
    def test_the_k_and_long_forms_survive_alongside_it(self, value):
        """Most people still write "$500k"; this must stay the common form."""
        forms = self._money(value)
        assert any(f.endswith("k") for f in forms)
        assert any("," in f for f in forms)

    def test_a_value_that_is_not_round_is_never_written_in_millions(self):
        assert not any("M" in f or "million" in f for f in self._money(95_000))

    def test_the_stated_figure_always_matches_the_gold_bound(self):
        """The whole point: "0.4M" in the text must gold 400000, not 4000000."""
        random.seed(31)
        checked = 0
        for _ in range(1500):
            bounds, phrase = _range_phrase(PRICE_NUMBERS)
            values = {v for v in bounds.values() if v}
            for frac in re.findall(r"\b(0\.\d+)\s?(?:M|million)", phrase):
                checked += 1
                assert int(float(frac) * 1_000_000) in values, f"{phrase!r} -> {bounds}"
        assert checked, "no sub-million M-notation generated at all"


class TestBudgetMagnitude:
    """"from $30M to $40M" came back as 3,000,000 - 4,000,000: a factor of ten, twice.

    Not a parse failure. The sampler stopped at $4.9M, so every M-notation figure the set
    ever produced had a single digit before the decimal point -- integer parts 0 through 8,
    never two. "$30M" was a token shape the model had never seen and "$3.0M", which it had
    seen hundreds of times, is one dot away. Commercial real estate does not stop at $5M.
    """

    # Anything after a decimal point is a fractional part, not a second figure: without
    # the lookbehind, "0.15M" reads as the two-digit "15M" and the gap hides itself.
    M_FIGURE = re.compile(r"(?<![\d.])(\d+)(?:\.\d+)?\s?(?:M\b|million\b|mil\b)", re.I)

    def _values(self, n: int = 20000, seed: int = 3) -> list[int]:
        random.seed(seed)
        return [_price_value() for _ in range(n)]

    def test_budgets_reach_tens_of_millions(self):
        values = self._values()
        assert max(values) >= 100_000_000, f"tops out at {max(values):,}"
        two_digit = [v for v in values if 10_000_000 <= v < 100_000_000]
        assert len(two_digit) / len(values) >= 0.08, f"only {len(two_digit)} of {len(values)}"

    def test_the_common_bands_still_dominate(self):
        """A widened sampler must not turn an ordinary $500k budget into the rare case."""
        values = self._values()
        assert sum(1 for v in values if v < 1_000_000) / len(values) >= 0.5

    def test_hundreds_of_millions_stay_rarer_than_tens(self):
        values = self._values()
        tens = sum(1 for v in values if 10_000_000 <= v < 100_000_000)
        hundreds = sum(1 for v in values if v >= 100_000_000)
        assert 0 < hundreds < tens, f"tens {tens}, hundreds {hundreds}"

    def test_two_digit_millions_are_actually_written_that_way(self):
        """The band is only worth anything if ``_fmt_money`` renders it as "$30M"."""
        random.seed(7)
        digits = collections.Counter()
        for _ in range(8000):
            for match in self.M_FIGURE.finditer(_fmt_money(_price_value())):
                digits[len(match.group(1))] += 1
        assert digits[2] >= 100, dict(digits)
        assert digits[1] > digits[2] > digits[3], dict(digits)

    # The whole figure, fraction included, so "12.5M" is checked as 12.5 rather than 12.
    M_VALUE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s?(?:M\b|million\b|mil\b)", re.I)

    def test_a_stated_million_figure_always_equals_its_gold(self):
        """The failure mode itself: "$30M" in the text must gold 30000000."""
        random.seed(13)
        checked = 0
        for _ in range(8000):
            bounds, phrase = _range_phrase(PRICE_NUMBERS)
            for match in self.M_VALUE.finditer(phrase):
                checked += 1
                # round, not int: float("65.6") * 1e6 is 65599999.99, and truncating it
                # fails a figure the generator got exactly right.
                stated = round(float(match.group(1)) * 1_000_000)
                assert stated in bounds.values(), f"{phrase!r} -> {bounds}"
        assert checked, "no M-notation generated at all"


class TestRangeEndpointsAgree:
    """The two ends of a range are one client's budget, not two independent draws.

    ``low + sample()`` was tolerable while budgets stopped at $5M -- "between $25,000 and
    $4.5M" is odd, not absurd. At $150M the same code pairs a $45,000 floor with a $92.5M
    ceiling, which nobody writes and which teaches that the two figures are unrelated.
    """

    def _ranges(self, numbers, n: int = 8000, seed: int = 5):
        random.seed(seed)
        out = []
        for _ in range(n):
            bounds, phrase = _range_phrase(numbers)
            if (bounds.get("min") is not None and bounds.get("max") is not None
                    and bounds["min"] != bounds["max"]):
                out.append((bounds, phrase))
        return out

    @pytest.mark.parametrize("numbers", [PRICE_NUMBERS, SQFT_NUMBERS])
    def test_the_ceiling_stays_within_a_few_multiples_of_the_floor(self, numbers):
        ranges = self._ranges(numbers)
        assert ranges, "no two-sided ranges generated"
        for bounds, phrase in ranges:
            ratio = bounds["max"] / bounds["min"]
            assert 1.0 < ratio <= 4.0, f"{phrase!r} -> {bounds} ({ratio:.1f}x)"

    def test_the_ceiling_is_a_figure_someone_would_say(self):
        """A million-and-up ceiling has to be a clean multiple, or M-notation gets ugly.

        $1,905,000 is what a floor-derived grain produces from a $950,000 floor, and
        ``_fmt_money`` writes it as "$1905k".
        """
        for bounds, phrase in self._ranges(PRICE_NUMBERS):
            high = bounds["max"]
            grain = 100_000 if high >= 1_000_000 else 5_000 if high >= 100_000 else 500
            assert high % grain == 0, f"{phrase!r} -> {high:,}"


class TestRealWorldMessageForms:
    """Wordings that reached production and had zero coverage in the v3 set.

    Measured on v3's train.jsonl: 0 city nicknames, 0 bare state names, 0 uppercase K,
    0 "bucks"/"grand", 0 exclamation marks, 2 unsupported requirements. Each of the three
    reported failures was a message built entirely from that missing vocabulary.
    """

    def _messages(self, n: int = 1500, seed: int = 17) -> list[str]:
        return [e["user_input"] for e in _examples(n=n, seed=seed)]

    def test_city_nicknames_appear(self):
        """"located in SF" extracted nothing: no v3 message contained a nickname."""
        text = " || ".join(self._messages()).lower()
        found = {a for a in CITY_ALIASES if a.lower() in text}
        assert len(found) >= 5, f"only {sorted(found)}"

    def test_a_nickname_resolves_to_the_canonical_city(self):
        random.seed(23)
        seen = {}
        for _ in range(2000):
            gold, place = _place()
            if place in CITY_ALIASES:
                seen[place] = gold
        assert seen, "no aliases generated"
        for alias, gold in seen.items():
            assert gold == CITY_ALIASES[alias], f"{alias!r} golded {gold!r}"

    def test_bare_state_names_appear(self):
        """"shopping mall in California" -- v3 only ever saw cities."""
        text = " || ".join(self._messages())
        assert sum(1 for s in STATES if s in text) >= 5

    def test_uppercase_k_and_bare_thousands_appear(self):
        """"costs more than 100K" and "less than 10K bucks" -- v3 wrote only "$100k"."""
        text = " || ".join(self._messages())
        assert re.search(r"\d\s?K\b", text), "no uppercase K"
        assert re.search(r"(?<![$\d])\b\d+k\b", text), "no thousands without a dollar sign"

    def test_informal_money_words_appear(self):
        text = " || ".join(self._messages()).lower()
        assert "grand" in text or "bucks" in text

    def test_unsupported_requirements_appear_and_are_never_extracted(self):
        """"3 floor", "need to have good view" belong in no field, so gold omits them.

        The stray numbers are the point -- "3 floors" is the shape that gets misread as a
        size when the set contains no example of a clause being left out.
        """
        examples = _examples(n=1500, seed=17)
        with_distractor = [
            e for e in examples
            if any(d in e["user_input"].lower() for d in (d.lower() for d in DISTRACTORS))
        ]
        assert len(with_distractor) >= 40, f"only {len(with_distractor)} carry one"
        for e in with_distractor:
            assert set(e["target"]["extracted"]) <= set(QUESTION_KEYS)

    def test_punctuation_and_casing_vary(self):
        messages = self._messages()
        assert any("!" in m for m in messages), "no exclamation marks"
        assert any(m and m[0].isupper() for m in messages), "nothing sentence-cased"

    def test_every_example_still_validates(self):
        """None of the above may produce an example the trainer would reject."""
        for example in _examples(n=1500, seed=17):
            assert validate(example, set(QUESTION_KEYS), set(REQUIRED)) is None


class TestNumberAndUnitWordings:
    """Forms the eval scores, or a client types, that v3 never generated."""

    def _phrases(self, key: str, n: int = 4000, seed: int = 1) -> str:
        random.seed(seed)
        return " || ".join(_field_fragment(key, PROPERTY_TYPES, PHRASINGS)[1] for _ in range(n))

    def test_money_written_in_words(self):
        """"half a million" and "a quarter of a million" have been eval turns since r1."""
        text = self._phrases("price").lower()
        assert "half a million" in text
        assert "quarter of a million" in text

    def test_every_square_foot_unit_appears(self):
        text = self._phrases("size_sqft")
        for unit in ("sqft", "sq ft", "sq. ft.", "square feet", "square footage"):
            assert unit in text, f"{unit!r} never generated"
        assert re.search(r"\d[\d,]*\s?SF\b", text), "SF as a unit never generated"

    def test_sf_is_generated_in_both_senses(self):
        """SF means square feet far more often than San Francisco in this industry.

        Both are in the set on purpose: the disambiguating signal is a figure immediately
        before it, and only context can carry that.
        """
        sizes = self._phrases("size_sqft")
        assert re.search(r"\d[\d,]*\s?SF\b", sizes)
        assert "SF" in CITY_ALIASES and CITY_ALIASES["SF"] == "San Francisco"

    def test_approximate_qualifiers_appear_without_changing_the_bound(self):
        random.seed(5)
        softened = 0
        for _ in range(3000):
            bounds, phrase = _range_phrase(PRICE_NUMBERS)
            if any(p.strip() in phrase for p in ("around", "about", "roughly", "approximately")):
                softened += 1
                assert bounds, "a softened figure still states a bound"
        assert softened, "no approximate wording generated"

    def test_hyphenated_ranges_appear(self):
        random.seed(9)
        phrases = [_range_phrase(SQFT_NUMBERS)[1] for _ in range(3000)]
        assert any(re.search(r"\d[\d,]*\s?-\s?\d", p) for p in phrases)

    def test_a_written_out_figure_still_golds_the_number(self):
        """"half a million" must gold 500000, not a string."""
        random.seed(11)
        for _ in range(4000):
            bounds, phrase = _range_phrase(PRICE_NUMBERS)
            if "half a million" in phrase:
                assert 500_000 in bounds.values(), f"{phrase!r} -> {bounds}"
            if "quarter of a million" in phrase:
                assert 250_000 in bounds.values(), f"{phrase!r} -> {bounds}"


class TestBoundDirectionVocabulary:
    """r6 scored ``bound-direction`` at 0.375 value accuracy on v3, v4 f16 and v4 q4 alike.

    Identical to three decimals across two training runs and two quantizations, so neither
    noise nor the quantizer: the wordings were simply not in the set. Counted on that
    train.jsonl -- ``ceiling`` 0, ``shy of`` 0, ``nothing below`` 0, ``no lower`` 0,
    ``at minimum`` 0 -- and all 24 hits for ``floor`` were ``ground floor`` / ``top floor``,
    a storey rather than a budget floor.

    The failures line up with the gaps one for one. ``nothing over $2M`` scored correct and
    ``nothing below 5,000 sqft`` did not, because the max list carried a negated form and
    the min list carried none; the model had learned to negate in one direction only.
    """

    def _phrases(self, numbers, n: int = 6000, seed: int = 2):
        random.seed(seed)
        return [_range_phrase(numbers) for _ in range(n)]

    # Every negated form in these lists leads with the negator, so a prefix test is exact.
    NEGATORS = ("no ", "not ", "never ", "nothing ")

    def _negated(self, pool: list[str]) -> list[str]:
        return [p for p in pool if p.startswith(self.NEGATORS)]

    def test_both_directions_offer_the_same_breadth(self):
        """v2 had 4 upper wordings against 3 lower and inverted every unseen lower one."""
        assert len(MIN_PHRASES) == len(MAX_PHRASES)

    def test_every_negated_wording_has_a_counterpart_in_the_other_direction(self):
        """Asymmetry here is not a style question; it is what "nothing below" failed on.

        The count is what matters, not the pairing -- a model that has seen five negated
        ceilings and one negated floor learns that a negation means a ceiling.
        """
        lower, upper = self._negated(MIN_PHRASES), self._negated(MAX_PHRASES)
        assert len(lower) == len(upper), f"min {lower}\nmax {upper}"
        assert len(lower) >= 4, "too few negated forms for either side to generalise"

    def test_floor_states_a_lower_bound_and_ceiling_an_upper_one(self):
        """The two words the set never used in their bound sense.

        Neither is inferable: no amount of generalisation tells a model that a budget
        floor is a minimum, because the word carries that meaning lexically or not at all.
        """
        seen = collections.Counter()
        for bounds, phrase in self._phrases(PRICE_NUMBERS):
            # A reversed range states both, and is covered by the range tests below.
            if "floor" in phrase and "ceiling" not in phrase:
                seen["floor"] += 1
                assert bounds.get("min") is not None, f"{phrase!r} -> {bounds}"
            if "ceiling" in phrase and "floor" not in phrase:
                seen["ceiling"] += 1
                assert bounds.get("max") is not None, f"{phrase!r} -> {bounds}"
        assert seen["floor"] and seen["ceiling"], seen

    def test_the_storey_sense_of_floor_survives_alongside_the_bound_sense(self):
        """Both senses stay in the set, as with "SF" in SQFT_UNITS.

        Teaching the bound sense by removing the other one would only move the ambiguity:
        "ground floor only" is a real thing clients write, and it belongs in no field.
        """
        text = " || ".join(e["user_input"] for e in _examples(n=1500, seed=17)).lower()
        assert "ground floor" in text or "top floor" in text

    def test_a_range_may_be_stated_ceiling_first(self):
        """Templates, not samples: position must not encode direction anywhere.

        Every ``between`` wording put {lo} first, so order and comparator never disagreed
        and all three r6 models read the order instead -- "lower than $2M, higher than
        $500K" came back as min $2M / max $500K, both comparators ignored.
        """
        for template in BETWEEN_PHRASES:
            assert template.index("{lo}") < template.index("{hi}"), template
        for template in REVERSED_BETWEEN_PHRASES:
            assert template.index("{hi}") < template.index("{lo}"), template

    def _matches_any(self, phrase: str, templates: list[str]) -> bool:
        for template in templates:
            parts = [re.escape(p) for p in re.split(r"\{lo\}|\{hi\}", template)]
            if re.fullmatch(".+?".join(parts), phrase):
                return True
        return False

    def test_the_ceiling_first_form_is_a_minority_but_a_real_one(self):
        """Held below the {lo}-first share on purpose: over-weighting it would relocate
        the positional prior rather than remove it."""
        reversed_seen = forward = 0
        for _, phrase in self._phrases(SQFT_NUMBERS):
            reversed_seen += self._matches_any(phrase, REVERSED_BETWEEN_PHRASES)
            forward += self._matches_any(phrase, BETWEEN_PHRASES)
        assert forward and reversed_seen, f"forward {forward}, reversed {reversed_seen}"
        share = reversed_seen / (forward + reversed_seen)
        assert 0.15 <= share <= 0.40, f"{share:.1%} of ranges state the ceiling first"

    def test_no_range_ever_golds_a_min_above_its_max(self):
        """The failure mode a reversed template invites: swap the figures, not the words."""
        for numbers in (PRICE_NUMBERS, SQFT_NUMBERS):
            for bounds, phrase in self._phrases(numbers):
                if bounds.get("min") is not None and bounds.get("max") is not None:
                    assert bounds["min"] <= bounds["max"], f"{phrase!r} -> {bounds}"


class TestBoundWordingEvalSeparation:
    """``bound-direction`` turns must stay wordings the generator does not emit.

    The sibling of TestSynonymEvalSeparation, and the same mistake it exists to catch: a
    turn scored on a phrasing the set produces measures recall of a list. Two of the
    phrasings added for this fix were a turn verbatim -- "nothing over {v}" and "just shy
    of {v}" -- and one of those turns already scored correct, so the pair bought a
    guaranteed pass and cost the only honest reading of the category.

    Scoped to ``bound-direction`` deliberately. Other categories reuse "up to" and "at
    least" freely, and should: those are the core comparators, and a set that withheld
    them would be teaching nothing. This category is the one that exists to ask whether
    direction survives an unseen wording.

    One exemption, taken knowingly: ``floor`` and ``ceiling`` are taught, and two turns
    use them. A lexical item has no unseen-wording generalisation to test -- see
    TestBoundDirectionVocabulary -- so those turns now measure vocabulary, and the rule
    below only holds them to not being a whole template instance.
    """

    # A placeholder stands for a figure, not for arbitrary text. With ``.+?`` the one-word
    # templates swallow whole sentences: "{v} ceiling" would "match" `$500K floor, $2M
    # ceiling` and the rule would flag every turn that ends in a bound word.
    FIGURE = (r"[~$]?[\d,.]+\s?(?:k|K|M|mil|million|sqft|sq\.? ?ft\.?|SF|sf|"
              r"square feet|square foot|square footage)?")

    def _turns(self):
        lines = EVAL_DATASET_PATH.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        return [r for r in rows if r["category"] == "bound-direction"]

    def test_the_category_exists(self):
        assert self._turns(), "no bound-direction turns; the weakest cell is unmeasurable"

    def test_no_turn_is_an_instance_of_a_generated_wording(self):
        templates = MIN_PHRASES + MAX_PHRASES + BETWEEN_PHRASES + REVERSED_BETWEEN_PHRASES
        for row in self._turns():
            for template in templates:
                parts = re.split(r"\{v\}|\{lo\}|\{hi\}", template)
                pattern = self.FIGURE.join(re.escape(p) for p in parts)
                assert not re.fullmatch(pattern, row["user_input"], re.I), (
                    f"{row['id']} scores the training wording {template!r}"
                )


class TestLocationLabels:
    def test_gold_never_invents_a_state(self):
        """A phrasing that names only the city must not be labelled "City, ST"."""
        random.seed(11)
        states = {state for _, state in CITIES}
        for _ in range(300):
            gold, fragment = _field_fragment("location", PROPERTY_TYPES, PHRASINGS)
            if "," in gold:
                _, state = gold.split(",", 1)
                assert state.strip() in fragment, f"{gold!r} not stated in {fragment!r}"
            else:
                # No state in gold, so the fragment must not name one either.
                assert not any(f", {s}" in fragment for s in states)


class TestGeneratedExamples:
    def test_all_examples_validate(self):
        for example in _examples():
            assert validate(example, set(QUESTION_KEYS), set(REQUIRED)) is None

    def test_extracted_and_skipped_never_overlap(self):
        for example in _examples():
            target = example["target"]
            assert not set(target["extracted"]) & set(target["skipped_fields"])

    def test_next_question_follows_the_ordering_rule(self):
        for example in _examples():
            answered = set(example["current_criteria"]) | set(example["target"]["extracted"])
            answered.discard("_skipped_fields")
            skipped = set(example["target"]["skipped_fields"])
            assert example["next_question_key"] == _next_question_key(
                answered, skipped, ORDERED_REQUIRED)

    def test_never_re_extracts_what_current_criteria_already_holds(self):
        """Restating a stored value is only correct when the message is a correction.

        Everywhere else it is the over-emission P2 measured: copying the payload back
        instead of reading the message.
        """
        for example in _examples():
            if example["shape"] == "correction":
                continue
            prior = set(example["current_criteria"]) - {"_skipped_fields"}
            assert not prior & set(example["target"]["extracted"])

    def test_a_correction_restates_a_field_that_is_already_answered(self):
        """The inverse: a correction MUST overlap current_criteria, or it teaches nothing."""
        corrections = [e for e in _examples(n=1200, seed=7) if e["shape"] == "correction"]
        assert corrections, "no correction examples generated"
        for example in corrections:
            prior = set(example["current_criteria"]) - {"_skipped_fields"}
            extracted = set(example["target"]["extracted"])
            assert extracted, f"correction extracted nothing: {example['user_input']!r}"
            assert extracted <= prior, "a correction must restate an answered field"

    def test_corrections_come_with_and_without_an_explicit_marker(self):
        """"100sqft" after a wrong size is a correction whether or not the user says so."""
        corrections = [e for e in _examples(n=1200, seed=7) if e["shape"] == "correction"]
        markers = ("actually", "scratch that", "make it", "make that", "i meant",
                   "no,", "change that", "let's say", "correction:", "update that")
        marked = [e for e in corrections
                  if any(m in e["user_input"].lower() for m in markers)]
        assert marked, "no marked corrections"
        assert len(marked) < len(corrections), "every correction is marked; the bare form failed"

    def test_a_real_share_of_examples_extract_nothing(self):
        # Teaching restraint is the whole point; an all-fields set would train the
        # over-emission that P2 measured.
        examples = _examples()
        empty = sum(1 for e in examples if not e["target"]["extracted"])
        assert 0.2 <= empty / len(examples) <= 0.5

    def test_examples_are_sparse_on_average(self):
        examples = _examples()
        mean_fields = sum(len(e["target"]["extracted"]) for e in examples) / len(examples)
        assert mean_fields < 2.0


class TestChatRecord:
    def test_uses_the_production_prompt_builder(self, questions):
        example = _examples(n=1)[0]
        record = to_chat_record(example, questions)
        assert [m["role"] for m in record["messages"]] == ["system", "user", "assistant"]
        # Constant content first, so a served prefix cache keeps hitting.
        assert "JSON Schema" in record["messages"][0]["content"]
        assert example["user_input"] in record["messages"][1]["content"]

    def test_completion_is_the_target_json(self, questions):
        example = _examples(n=1)[0]
        record = to_chat_record(example, questions)
        assert json.loads(record["messages"][-1]["content"]) == example["target"]

    def test_completion_carries_no_recomputed_fields(self, questions):
        # The schema asks for two fields; training data must not teach a third.
        for example in _examples(n=50):
            completion = json.loads(to_chat_record(example, questions)["messages"][-1]["content"])
            assert set(completion) == {"extracted", "skipped_fields"}


class TestSquareYards:
    """"1500 yard ground" returned no size at all, and the set is why.

    All 22 occurrences of "yard" were ``fenced yard``, a ``DISTRACTORS`` entry, so the
    only thing the word had ever been used for was noise. Square yards are the everyday
    plot unit in South-Asian markets, and this is the one unit where the stated figure and
    the gold figure differ -- 1,500 yards is 13,500 sqft -- so it is the only place the
    model has to convert rather than copy.
    """

    # Longest first, so "square yards" is not consumed as "yards" with a stray prefix.
    _UNIT = "|".join(re.escape(u) for u in sorted(SQYD_UNITS, key=len, reverse=True))
    FIGURE = re.compile(rf"([\d,]+)\s+(?:{_UNIT})\b")

    def _phrases(self, n: int = 6000, seed: int = 8):
        random.seed(seed)
        return [_range_phrase(SQFT_NUMBERS) for _ in range(n)]

    def test_yards_are_generated_at_all(self):
        stated = [p for _, p in self._phrases() if self.FIGURE.search(p)]
        assert len(stated) >= 100, f"only {len(stated)} yard phrasings in 6000"

    def test_every_unit_spelling_appears(self):
        # ``\b`` cannot follow "sq. yd." -- the trailing dot is not a word character, so a
        # boundary needs a word character after it and a space never provides one.
        text = " || ".join(p for _, p in self._phrases(n=12000))
        for unit in SQYD_UNITS:
            assert re.search(rf"\d\s+{re.escape(unit)}(?!\w)", text), f"{unit!r} never seen"

    def test_a_stated_yard_figure_golds_nine_times_itself(self):
        """The whole point. "1,500 yards" must gold 13500, not 1500."""
        checked = 0
        for bounds, phrase in self._phrases():
            match = self.FIGURE.search(phrase)
            if not match:
                continue
            checked += 1
            stated = int(match.group(1).replace(",", "")) * SQFT_PER_SQYD
            assert stated in bounds.values(), f"{phrase!r} -> {bounds}"
        assert checked, "no yard figure generated at all"

    def test_a_yard_figure_is_never_fractional(self):
        """Rounding the text would put the gold out by a few sqft, silently."""
        for _, phrase in self._phrases():
            match = self.FIGURE.search(phrase)
            if match:
                assert "." not in match.group(1), phrase

    def test_yards_never_share_a_phrase_with_a_second_figure(self):
        """Each side of a range renders independently, so no shared unit can be agreed.

        "9,000-1,500 yards" is what a hyphenated range produces when the high side picks
        yards and the low side does not, and no reading of that text yields the gold.
        """
        for _, phrase in self._phrases():
            if any(unit in phrase for unit in SQYD_UNITS):
                assert len(re.findall(r"\d[\d,]*", phrase)) == 1, phrase

    def test_a_bare_yard_answer_is_exact_like_any_bare_size(self):
        random.seed(12)
        seen = 0
        for _ in range(4000):
            bounds, fragment = _field_fragment("size_sqft", PROPERTY_TYPES, PHRASINGS)
            match = self.FIGURE.search(fragment)
            if match and bounds.get("min") == bounds.get("max"):
                seen += 1
                assert bounds["min"] == int(match.group(1).replace(",", "")) * SQFT_PER_SQYD
        assert seen, "no exact yard answer generated"

    def test_the_fenced_yard_distractor_still_exists(self):
        """Both senses stay in the set; the disambiguating signal is the figure.

        Removing the distractor would teach "yard means size" unconditionally, which is
        the mirror of the bug -- "a fenced yard would be nice" states no size at all.
        """
        assert any("yard" in d for d in DISTRACTORS)

    def test_money_is_untouched_by_the_solo_renderer(self):
        """``render_solo`` exists for size; price must render exactly as it always did."""
        assert PRICE_NUMBERS.render_solo is PRICE_NUMBERS.render


class TestAmbiguousTypeWords:
    """A type word that also appears with a non-type meaning must win on context.

    ``ground`` is a configured ``land`` phrasing and ``ground floor`` is a distractor. A
    flat draw over land's phrasings put ``ground`` in ~8 messages against 18 for ``ground
    floor``, so the token's own statistics said "ignore me", and "warehouse, restaurant,
    shop, 1500 yard ground" came back from production with no ``land`` at all.
    """

    def _messages(self, n: int = 2500, seed: int = 17) -> list[str]:
        return [e["user_input"] for e in _examples(n=n, seed=seed)]

    def test_every_weighted_phrasing_is_one_the_generator_can_draw(self):
        """A typo here weights nothing and fails silently."""
        for option, phrasings in AMBIGUOUS_TYPE_PHRASINGS.items():
            assert option in PHRASINGS, f"{option} is not a configured type"
            for phrase in phrasings:
                assert phrase in PHRASINGS[option], f"{option}: {phrase!r} is not a phrasing"

    def test_the_type_sense_outweighs_the_distractor_sense(self):
        """Aggregated over seeds on purpose.

        One 2500-example draw puts both senses in the teens, where the winner is decided
        by the draw rather than by the weighting -- five seeds at the old 4x weight ran
        16v19, 18v16, 25v7, 11v14, 17v16. A property that only holds on a lucky seed is
        not the property this fix needs.
        """
        land = storey = 0
        for seed in (17, 3, 99):
            text = " || ".join(self._messages(seed=seed))
            land += len(re.findall(r"\bground\b(?!\s+floor)", text, re.I))
            storey += len(re.findall(r"\bground\s+floor\b", text, re.I))
        assert land > storey * 1.1, f"ground-as-land {land}, ground floor {storey}"

    def test_the_storey_sense_is_not_driven_out(self):
        """Weighting the type sense must not remove the collision it exists to teach."""
        text = " || ".join(self._messages())
        assert re.search(r"\bground\s+floor\b", text, re.I)

    def test_a_weighted_phrasing_still_golds_its_option(self):
        for example in _examples(n=2500, seed=17):
            if re.search(r"\bground\b(?!\s+floor)", example["user_input"], re.I):
                assert "land" in example["target"]["extracted"].get("property_type", []), (
                    example["user_input"]
                )

    def test_the_other_phrasings_are_not_crowded_out(self):
        """Weight 4 of ~9, drawn half the time -- a boost, not a takeover."""
        random.seed(4)
        drawn = collections.Counter()
        for _ in range(8000):
            picked, words = _type_words(PROPERTY_TYPES, PHRASINGS)
            if picked == ["land"]:
                drawn[words] += 1
        assert drawn, "land was never the only type picked"
        assert drawn["ground"] / sum(drawn.values()) < 0.35, drawn.most_common(5)
        assert len([w for w in drawn if w != "ground"]) >= 5, drawn


class TestEvalCollisionGuard:
    """The hold-out has to survive ``_rough_up``, which runs after the example is built.

    Comparing raw strings let seven rows through in r6: "that's everything" four ways
    (upper-cased, sentence-cased, with a full stop, with "!!") and "yes that's correct"
    three. Both are ``complete`` turns, where the wording is the entire signal, so half
    that eval category was scoring recall -- and the generator's own rejection count
    reported them held out the whole time.
    """

    @pytest.mark.parametrize("roughened", [
        "THAT'S EVERYTHING", "That's everything", "That's everything.",
        "That's everything!!", "that's everything please", "  that's everything  ",
    ])
    def test_every_form_rough_up_can_produce_still_collides(self, roughened):
        assert collision_key(roughened) == collision_key("that's everything")

    def test_a_different_wording_does_not_collide(self):
        """Folding case and punctuation, not meaning -- an over-eager key would reject
        legitimate variety and quietly shrink the set."""
        assert collision_key("that's all") != collision_key("that's everything")
        assert collision_key("up to $2 million") != collision_key("up to $3 million")

    def test_a_blank_message_is_not_treated_as_a_held_out_wording(self):
        """The empty and whitespace turns score a behaviour, not a phrasing.

        Holding them out would leave the set with no example of a blank message at all,
        so the eval would go on scoring behaviour that training had stopped teaching.
        """
        assert collision_key("") == ""
        assert collision_key("   \n ") == ""
        assert "" not in eval_input_keys(Path(EVAL_DATASET_PATH))

    def test_the_hold_out_covers_every_eval_turn_that_has_a_wording(self):
        rows = [json.loads(line) for line
                in Path(EVAL_DATASET_PATH).read_text(encoding="utf-8").splitlines()
                if line.strip()]
        keys = eval_input_keys(Path(EVAL_DATASET_PATH))
        for row in rows:
            key = collision_key(row["user_input"])
            assert not key or key in keys, f"{row['id']} is not held out"

    def test_the_guard_is_load_bearing_and_the_raw_comparison_was_not_enough(self):
        """Two claims, both on real generator output at the seed ``main`` uses.

        A guard that never fires proves nothing, and one whose every catch the old raw
        comparison would also have made is not a fix. Both have to hold, or this class is
        testing a key nothing routes through.
        """
        keys = eval_input_keys(Path(EVAL_DATASET_PATH))
        collided = [e["user_input"] for e in _examples(n=2500, seed=17)
                    if collision_key(e["user_input"]) in keys]
        assert len(collided) >= 20, f"only {len(collided)} collisions in 2500 draws"

        raw = {json.loads(line)["user_input"] for line
               in Path(EVAL_DATASET_PATH).read_text(encoding="utf-8").splitlines()
               if line.strip()}
        assert [t for t in collided if t not in raw], "no roughened collision in the sample"


class TestSynonymEvalSeparation:
    """The generated phrasings are the training vocabulary; the eval must not reuse them.

    Scoring a synonym turn on a wording the generator emits measures recall of that list,
    not generalisation. This project has made that mistake twice already -- 14 refusal
    strings, then 4 comparator phrasings -- and both times the eval looked healthy while
    the model had learned a list. The phrasings file is regenerated, so overlap can appear
    without anyone editing a turn.
    """

    def _synonym_turns(self):
        lines = EVAL_DATASET_PATH.read_text(encoding="utf-8").splitlines()
        rows = [json.loads(line) for line in lines if line.strip()]
        return [r for r in rows if r["category"] == "property-synonym"]

    def test_the_category_exists(self):
        assert self._synonym_turns(), "no property-synonym turns; the fix is unmeasurable"

    def test_turns_avoid_every_generated_phrasing(self):
        phrasings = load_phrasings(PHRASINGS_PATH)
        trained = {p.lower() for pool in phrasings.values() for p in pool} | set(phrasings)
        for row in self._synonym_turns():
            text = row["user_input"].lower()
            reused = sorted(w for w in trained if w in text)
            assert not reused, f"{row['id']} reuses training vocabulary: {reused}"

    def test_gold_is_a_configured_option(self):
        questions = json.loads(Path(QUESTIONS_PATH).read_text(encoding="utf-8"))
        options = set(property_type_values(questions))
        for row in self._synonym_turns():
            for value in row["gold"]["extracted"]["property_type"]:
                assert value in options, f"{row['id']} golds {value!r}, not an option"
