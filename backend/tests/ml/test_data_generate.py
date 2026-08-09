"""Invariants for the programmatic training-data generator.

A bug here is invisible: it produces plausible JSONL that silently teaches the model the
wrong behaviour. These tests pin the properties the P2 baseline says matter most.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from ml.data.generate import (
    CITIES,
    FIELD_LABELS,
    _field_fragment,
    _next_question_key,
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
        for example in _examples():
            prior = set(example["current_criteria"]) - {"_skipped_fields"}
            assert not prior & set(example["target"]["extracted"])

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
