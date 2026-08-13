"""Unit tests for the intake eval scoring.

These pin the numbers a results row is built from. A change here should be a deliberate
diff, not a quiet shift in what a published metric means.
"""

from __future__ import annotations

import json

import pytest

from app.schemas.llm_intake_parse import LlmParseModelOutput
from pipeline.eval import metrics
from pipeline.eval.metrics import (
    aggregate,
    by_category,
    fmt,
    markdown_row,
    parse_raw_output,
    percentile,
    prf,
    ratio,
    score_turn,
    values_equal,
)

QUESTION_KEYS = ["location", "property_type", "listing_type", "price", "size_sqft"]
REQUIRED = ["location", "property_type", "listing_type", "price", "size_sqft"]


def _predicted(**kwargs) -> LlmParseModelOutput:
    return LlmParseModelOutput.model_validate(kwargs)


def _score(gold: dict, predicted: LlmParseModelOutput | None, **kwargs):
    return score_turn(
        turn_id="t",
        category="single-field",
        gold=gold,
        predicted=predicted,
        required_fields=REQUIRED,
        question_keys=QUESTION_KEYS,
        raw_json_valid=True,
        schema_valid=True,
        latency_ms=100.0,
        **kwargs,
    )


class TestValuesEqual:
    def test_strings_ignore_case_and_whitespace(self):
        assert values_equal("Austin, Texas", "  austin,   texas ")

    def test_strings_ignore_trailing_punctuation(self):
        assert values_equal("Denver", "denver.")

    def test_different_strings_are_unequal(self):
        assert not values_equal("Austin", "Houston")

    def test_int_and_float_unify(self):
        assert values_equal(2000000, 2000000.0)

    def test_lists_are_order_insensitive(self):
        assert values_equal(["Flex", "Warehouse"], ["Warehouse", "Flex"])

    def test_list_membership_still_matters(self):
        assert not values_equal(["Flex"], ["Flex", "Warehouse"])

    def test_null_bounds_count_as_absent(self):
        assert values_equal({"max": 5000}, {"min": None, "max": 5000})

    def test_present_bound_is_not_absent(self):
        assert not values_equal({"min": 1000, "max": 5000}, {"max": 5000})

    def test_booleans_do_not_collapse_into_numbers(self):
        assert not values_equal(True, 1)


class TestParseRawOutput:
    def test_clean_object_is_raw_and_schema_valid(self):
        raw_valid, schema_valid, parsed = parse_raw_output('{"extracted": {"location": "Austin"}}')
        assert (raw_valid, schema_valid) is not None
        assert raw_valid and schema_valid
        assert parsed is not None
        assert parsed.extracted == {"location": "Austin"}

    def test_fenced_json_is_not_raw_valid(self):
        # The provider's fence-stripper would hide this; the harness must not.
        raw_valid, schema_valid, parsed = parse_raw_output('```json\n{"extracted": {}}\n```')
        assert not raw_valid
        assert not schema_valid
        assert parsed is None

    def test_prose_before_json_is_not_raw_valid(self):
        raw_valid, _, _ = parse_raw_output('Sure! {"extracted": {}}')
        assert not raw_valid

    def test_valid_json_of_the_wrong_shape_is_not_schema_valid(self):
        raw_valid, schema_valid, parsed = parse_raw_output("[]")
        assert raw_valid
        assert not schema_valid
        assert parsed is None

    def test_empty_string_is_invalid(self):
        assert parse_raw_output("") == (False, False, None)

    def test_a_broken_schema_class_raises_instead_of_scoring_zero(self, monkeypatch):
        """Only ValidationError means "the model got it wrong".

        Under a bare ``except Exception`` a fault in LlmParseModelOutput itself -- a
        renamed field, a bad annotation -- reads as schema_valid=False on every turn. The
        run then completes and writes a plausible table of zeros, which is the one failure
        this harness must not produce quietly.
        """
        def exploding_validate(_raw):
            raise AttributeError("LlmParseModelOutput is broken")

        monkeypatch.setattr(
            metrics.LlmParseModelOutput, "model_validate_json", exploding_validate
        )
        with pytest.raises(AttributeError):
            parse_raw_output('{"extracted": {}, "skipped_fields": []}')


class TestFieldScoring:
    def test_exact_match_scores_clean(self):
        score = _score(
            {"extracted": {"location": "Austin, Texas"}, "skipped_fields": []},
            _predicted(extracted={"location": "austin, texas"}),
        )
        assert (score.field_tp, score.field_fp, score.field_fn) == (1, 0, 0)
        assert (score.value_correct, score.value_compared) == (1, 1)

    def test_over_emission_counts_as_false_positives(self):
        score = _score(
            {"extracted": {"location": "Austin"}, "skipped_fields": []},
            _predicted(
                extracted={
                    "location": "Austin",
                    "property_type": ["Office", "Retail"],
                    "listing_type": "Lease",
                },
            ),
        )
        assert (score.field_tp, score.field_fp, score.field_fn) == (1, 2, 0)

    def test_missing_field_counts_as_false_negative(self):
        score = _score(
            {"extracted": {"location": "Austin", "property_type": ["Office"]}},
            _predicted(extracted={"location": "Austin"}),
        )
        assert (score.field_tp, score.field_fp, score.field_fn) == (1, 0, 1)

    def test_right_key_wrong_value_is_a_hit_but_not_accurate(self):
        score = _score(
            {"extracted": {"price": {"max": 2000000}}},
            _predicted(extracted={"price": {"max": 3000000}}),
        )
        assert score.field_tp == 1
        assert (score.value_correct, score.value_compared) == (0, 1)

    def test_keys_outside_the_question_set_are_counted(self):
        score = _score(
            {"extracted": {"location": "Austin"}},
            _predicted(extracted={"location": "Austin", "made_up": "x"}),
        )
        assert score.invented_keys == 1
        assert score.field_fp == 1


class TestSkipScoring:
    def test_skip_recall(self):
        score = _score(
            {"extracted": {}, "skipped_fields": ["property_type"]},
            _predicted(skipped_fields=["property_type"]),
        )
        assert (score.skip_tp, score.skip_fp, score.skip_fn) == (1, 0, 0)

    def test_non_question_keys_are_ignored_like_production(self):
        # The rules block's illustrative phrases must not be scored as skips.
        score = _score(
            {"extracted": {}, "skipped_fields": ["property_type"]},
            _predicted(skipped_fields=["property_type", "no preference", "skip that"]),
        )
        assert (score.skip_tp, score.skip_fp, score.skip_fn) == (1, 0, 0)

    def test_skipping_a_field_the_user_answered_is_a_false_positive(self):
        score = _score(
            {"extracted": {"location": "Austin"}, "skipped_fields": []},
            _predicted(extracted={"location": "Austin"}, skipped_fields=["price"]),
        )
        assert (score.skip_tp, score.skip_fp, score.skip_fn) == (0, 1, 0)

    def test_carried_skips_must_be_repeated(self):
        score = _score(
            {"extracted": {}, "skipped_fields": ["property_type", "listing_type"]},
            _predicted(skipped_fields=["property_type"]),
        )
        assert (score.skip_tp, score.skip_fn) == (1, 1)


class TestNextQuestion:
    def test_correct_key(self):
        score = _score(
            {"extracted": {}, "next_question_key": "property_type"},
            _predicted(next_question={"key": "property_type", "text": "What type?"}),
        )
        assert score.next_question_correct is True

    def test_asking_when_nothing_remains_is_wrong(self):
        score = _score(
            {"extracted": {}, "next_question_key": None},
            _predicted(next_question={"key": "price", "text": "Budget?"}),
        )
        assert score.next_question_correct is False

    def test_scoring_can_be_disabled(self):
        score = _score(
            {"extracted": {}, "next_question_key": "price"},
            _predicted(),
            score_next_question=False,
        )
        assert score.next_question_correct is None


class TestUnparseableOutput:
    def test_counts_every_gold_field_as_missed(self):
        score = _score(
            {
                "extracted": {"location": "Austin", "property_type": ["Office"]},
                "skipped_fields": ["price"],
                "next_question_key": "listing_type",
            },
            None,
        )
        assert score.field_fn == 2
        assert score.field_tp == 0
        assert score.skip_fn == 1
        assert score.next_question_correct is False


class TestRates:
    def test_ratio_is_none_rather_than_zero_when_undefined(self):
        assert ratio(0, 0) is None
        assert ratio(1, 2) == 0.5

    def test_prf_is_all_none_with_no_observations(self):
        assert prf(0, 0, 0) == {"precision": None, "recall": None, "f1": None}

    def test_prf_computes_f1(self):
        result = prf(tp=1, fp=1, fn=0)
        assert result["precision"] == 0.5
        assert result["recall"] == 1.0
        assert result["f1"] == pytest.approx(2 / 3)

    def test_percentile_nearest_rank(self):
        assert percentile([1, 2, 3, 4, 5], 50) == 3
        assert percentile([1, 2, 3, 4, 5], 95) == 5

    def test_percentile_edges(self):
        assert percentile([], 50) is None
        assert percentile([7.0], 95) == 7.0


class TestAggregate:
    def test_empty_run_has_no_metrics(self):
        summary = aggregate([])
        assert summary.turns == 0
        assert summary.raw_json_valid_rate is None

    def test_rolls_up_across_turns(self):
        scores = [
            _score(
                {"extracted": {"location": "Austin"}},
                _predicted(extracted={"location": "Austin"}),
            ),
            _score(
                {"extracted": {"location": "Denver"}},
                _predicted(extracted={"location": "Miami"}),
            ),
        ]
        summary = aggregate(scores)
        assert summary.turns == 2
        assert summary.raw_json_valid_rate == 1.0
        assert summary.fields["recall"] == 1.0
        assert summary.value_accuracy == 0.5

    def test_groups_by_category(self):
        first = _score({"extracted": {}}, _predicted())
        second = score_turn(
            turn_id="s",
            category="skip",
            gold={"extracted": {}, "skipped_fields": ["price"]},
            predicted=_predicted(skipped_fields=["price"]),
            required_fields=REQUIRED,
            question_keys=QUESTION_KEYS,
            raw_json_valid=True,
            schema_valid=True,
            latency_ms=50.0,
        )
        grouped = by_category([first, second])
        assert set(grouped) == {"single-field", "skip"}
        assert grouped["skip"].skips["recall"] == 1.0


class TestFormatting:
    def test_undefined_metrics_render_as_na(self):
        assert fmt(None) == "n/a"
        assert fmt(0.5) == "0.500"

    def test_markdown_row_reports_na_for_an_empty_run(self):
        row = markdown_row("label", "model", "http://localhost:8080/v1", aggregate([]))
        assert row.startswith("| label | `model` |")
        assert "n/a" in row


class TestDatasetIntegrity:
    """The dataset is scored data, so a typo in it silently corrupts every row."""

    def test_every_turn_is_well_formed(self, dataset_rows, question_keys, required_keys):
        seen_ids = set()
        for row in dataset_rows:
            assert row["id"] not in seen_ids, f"duplicate id {row['id']}"
            seen_ids.add(row["id"])
            assert row["split"] in {"dev", "holdout"}
            assert isinstance(row["user_input"], str)
            gold = row["gold"]
            for key in gold["extracted"]:
                assert key in question_keys, f"{row['id']} extracts unknown key {key}"
            for key in gold["skipped_fields"]:
                assert key in required_keys, f"{row['id']} skips non-required key {key}"
            next_key = gold["next_question_key"]
            assert next_key is None or next_key in question_keys

    def test_gold_next_question_matches_the_ordering_rule(
        self, dataset_rows, ordered_required
    ):
        for row in dataset_rows:
            gold = row["gold"]
            answered = set(row["current_criteria"]) | set(gold["extracted"])
            skipped = set(gold["skipped_fields"])
            expected = next(
                (k for k in ordered_required if k not in answered and k not in skipped),
                None,
            )
            assert gold["next_question_key"] == expected, row["id"]

    def test_holdout_is_a_meaningful_slice(self, dataset_rows):
        holdout = [r for r in dataset_rows if r["split"] == "holdout"]
        assert len(holdout) >= 5
        assert len({r["category"] for r in holdout}) >= 5


@pytest.fixture
def dataset_rows():
    from pipeline.paths import EVAL_DATASET_PATH

    path = EVAL_DATASET_PATH
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


@pytest.fixture
def questions():
    from pipeline.paths import QUESTIONS_PATH

    return json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def question_keys(questions):
    return {q["key"] for q in questions}


@pytest.fixture
def required_keys(questions):
    return {q["key"] for q in questions if q.get("required")}


@pytest.fixture
def ordered_required(questions):
    rows = sorted((q for q in questions if q.get("required")), key=lambda q: q["order_index"])
    return [q["key"] for q in rows]
