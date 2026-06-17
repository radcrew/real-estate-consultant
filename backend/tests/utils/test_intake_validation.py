from app.utils.intake_validation import (
    compute_current_index,
    has_answer,
    merge_missing_fields,
)


class TestHasAnswer:
    def test_none_is_false(self):
        assert has_answer(None) is False

    def test_empty_string_is_false(self):
        assert has_answer("") is False

    def test_whitespace_string_is_false(self):
        assert has_answer("   ") is False

    def test_non_empty_string_is_true(self):
        assert has_answer("Austin") is True

    def test_empty_list_is_false(self):
        assert has_answer([]) is False

    def test_non_empty_list_is_true(self):
        assert has_answer(["office"]) is True

    def test_empty_dict_is_false(self):
        assert has_answer({}) is False

    def test_non_empty_dict_is_true(self):
        assert has_answer({"min": 100}) is True

    def test_zero_int_is_true(self):
        assert has_answer(0) is True

    def test_false_bool_is_true(self):
        assert has_answer(False) is True


class TestComputeCurrentIndex:
    def test_empty_questions_returns_zero(self):
        assert compute_current_index([], {"location": "Austin"}) == 0

    def test_non_dict_criteria_returns_zero(self):
        assert compute_current_index([{"key": "location"}], None) == 0

    def test_counts_answered_keys(self):
        questions = [{"key": "location"}, {"key": "size_sqft"}, {"key": "property_type"}]
        criteria = {"location": "Austin", "size_sqft": 5000}
        assert compute_current_index(questions, criteria) == 2

    def test_unanswered_not_counted(self):
        questions = [{"key": "location"}, {"key": "size_sqft"}]
        assert compute_current_index(questions, {}) == 0

    def test_skips_questions_without_string_key(self):
        questions = [{"key": None}, {"key": 42}, {"key": "location"}]
        assert compute_current_index(questions, {"location": "TX"}) == 1


class TestMergeMissingFields:
    def test_model_missing_overlaps_with_real_gaps(self):
        result = merge_missing_fields(
            merged_criteria={"location": "Austin"},
            required_fields=["location", "size_sqft", "property_type"],
            model_missing=["size_sqft"],
        )
        assert result == ["size_sqft"]

    def test_model_missing_no_overlap_falls_back_to_criteria_gaps(self):
        result = merge_missing_fields(
            merged_criteria={"location": "Austin"},
            required_fields=["location", "size_sqft"],
            model_missing=["property_type"],  # not in required_fields
        )
        assert result == ["size_sqft"]

    def test_empty_model_missing_returns_criteria_gaps(self):
        result = merge_missing_fields(
            merged_criteria={},
            required_fields=["location", "size_sqft"],
            model_missing=[],
        )
        assert set(result) == {"location", "size_sqft"}

    def test_skipped_fields_excluded(self):
        result = merge_missing_fields(
            merged_criteria={},
            required_fields=["location", "size_sqft"],
            model_missing=[],
            skipped_fields=["size_sqft"],
        )
        assert result == ["location"]

    def test_all_answered_returns_empty(self):
        result = merge_missing_fields(
            merged_criteria={"location": "Austin", "size_sqft": 5000},
            required_fields=["location", "size_sqft"],
            model_missing=[],
        )
        assert result == []
