"""Invariants for the programmatic training-data generator.

A bug here is invisible: it produces plausible JSONL that silently teaches the model the
wrong behaviour. These tests pin the properties the P2 baseline says matter most.
"""

from __future__ import annotations

import json
import random

import pytest

from ml.data.generate import (
    CITIES,
    _field_fragment,
    _next_question_key,
    make_example,
    to_chat_record,
    validate,
)

QUESTION_KEYS = ["location", "property_type", "listing_type", "price", "size_sqft",
                 "loading_docks"]
REQUIRED = ["location", "property_type", "listing_type", "price", "size_sqft"]


@pytest.fixture
def questions():
    import json as _json
    from pathlib import Path

    from ml.data.generate import DEFAULT_QUESTIONS

    return _json.loads(Path(DEFAULT_QUESTIONS).read_text(encoding="utf-8"))


def _examples(n: int = 400, seed: int = 3):
    random.seed(seed)
    return [
        make_example(
            question_keys=QUESTION_KEYS,
            required=REQUIRED,
            ordered_required=REQUIRED,
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
                "next_question": {"text": None},
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
                "next_question": {"text": None},
            }
        }
        assert "unknown key" in (validate(example, set(QUESTION_KEYS), set(REQUIRED)) or "")

    def test_rejects_skipping_a_non_required_key(self):
        example = {
            "target": {
                "extracted": {},
                "skipped_fields": ["loading_docks"],
                "next_question": {"text": None},
            }
        }
        assert "non-required" in (validate(example, set(QUESTION_KEYS), set(REQUIRED)) or "")

    def test_accepts_a_clean_example(self):
        example = {
            "target": {
                "extracted": {"location": "Austin"},
                "skipped_fields": ["price"],
                "next_question": {"text": "What type?"},
            }
        }
        assert validate(example, set(QUESTION_KEYS), set(REQUIRED)) is None


class TestLocationLabels:
    def test_gold_never_invents_a_state(self):
        """A phrasing that names only the city must not be labelled "City, ST"."""
        random.seed(11)
        states = {state for _, state in CITIES}
        for _ in range(300):
            gold, fragment = _field_fragment("location")
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
            assert example["next_question_key"] == _next_question_key(answered, skipped, REQUIRED)

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
        # P1 removed these from the schema; training data must not reintroduce them.
        for example in _examples(n=50):
            completion = json.loads(to_chat_record(example, questions)["messages"][-1]["content"])
            assert set(completion) == {"extracted", "skipped_fields", "next_question"}
