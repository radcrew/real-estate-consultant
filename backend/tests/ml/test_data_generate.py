"""Invariants for the programmatic training-data generator.

A bug here is invisible: it produces plausible JSONL that silently teaches the model the
wrong behaviour. These tests pin the properties the P2 baseline says matter most.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest

from ml.data.generate import (
    CITIES,
    CITY_ALIASES,
    DISTRACTORS,
    FIELD_LABELS,
    PRICE_NUMBERS,
    SQFT_NUMBERS,
    STATES,
    _field_fragment,
    _fmt_money,
    _next_question_key,
    _place,
    _range_phrase,
    _skip_label,
    load_phrasings,
    make_example,
    property_type_values,
    to_chat_record,
    validate,
)
from ml.paths import EVAL_DATASET_PATH, PHRASINGS_PATH, QUESTIONS_PATH

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
