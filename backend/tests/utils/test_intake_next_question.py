from app.utils.intake_next_question import (
    find_question_row_by_key,
    first_question_row_in_missing,
    match_row_for_text_suggestion,
    suggested_question_as_dict,
)

QUESTIONS = [
    {"key": "location", "type": "location", "text": "Where?"},
    {"key": "size_sqft", "type": "range", "text": "How big?"},
    {"key": "property_type", "type": "multiselect", "text": "What type?"},
]


class TestSuggestedQuestionAsDict:
    def test_dict_returned_as_is(self):
        d = {"key": "location"}
        assert suggested_question_as_dict(d) is d

    def test_non_dict_returns_empty(self):
        assert suggested_question_as_dict("location") == {}
        assert suggested_question_as_dict(None) == {}


class TestFindQuestionRowByKey:
    def test_found(self):
        row = find_question_row_by_key(QUESTIONS, "size_sqft")
        assert row is not None
        assert row["key"] == "size_sqft"

    def test_not_found_returns_none(self):
        assert find_question_row_by_key(QUESTIONS, "nonexistent") is None

    def test_empty_list_returns_none(self):
        assert find_question_row_by_key([], "location") is None


class TestMatchRowForTextSuggestion:
    def test_returns_suggested_key_row_when_found(self):
        row = match_row_for_text_suggestion(QUESTIONS, suggested_key="size_sqft", missing_fields=["location"])
        assert row["key"] == "size_sqft"

    def test_falls_back_to_first_missing_field(self):
        row = match_row_for_text_suggestion(QUESTIONS, suggested_key="nonexistent", missing_fields=["property_type"])
        assert row["key"] == "property_type"

    def test_non_string_suggested_key_falls_back(self):
        row = match_row_for_text_suggestion(QUESTIONS, suggested_key=None, missing_fields=["location"])
        assert row["key"] == "location"

    def test_no_match_and_empty_missing_returns_none(self):
        result = match_row_for_text_suggestion(QUESTIONS, suggested_key="nope", missing_fields=[])
        assert result is None


class TestFirstQuestionRowInMissing:
    def test_returns_first_matching_question(self):
        row = first_question_row_in_missing(QUESTIONS, ["size_sqft", "location"])
        assert row["key"] == "location"  # first in QUESTIONS order

    def test_empty_missing_returns_none(self):
        assert first_question_row_in_missing(QUESTIONS, []) is None

    def test_no_overlap_returns_none(self):
        assert first_question_row_in_missing(QUESTIONS, ["budget"]) is None
