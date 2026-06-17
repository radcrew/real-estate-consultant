from app.schemas.llm_intake_parse import (
    LlmOpeningQuestionOutput,
    LlmParseModelOutput,
    LlmParseNextQuestion,
)


class TestLlmParseNextQuestion:
    def test_defaults_none(self):
        obj = LlmParseNextQuestion()
        assert obj.key is None
        assert obj.text is None

    def test_whitespace_stripped_to_none(self):
        obj = LlmParseNextQuestion(key="  ", text="  ")
        assert obj.key is None
        assert obj.text is None

    def test_valid_key_and_text(self):
        obj = LlmParseNextQuestion(key=" location ", text=" Where? ")
        assert obj.key == "location"
        assert obj.text == "Where?"

    def test_non_string_coerced_to_none(self):
        obj = LlmParseNextQuestion(key=42, text=None)
        assert obj.key is None


class TestLlmOpeningQuestionOutput:
    def test_defaults_empty_string(self):
        obj = LlmOpeningQuestionOutput()
        assert obj.text == ""

    def test_text_stripped(self):
        obj = LlmOpeningQuestionOutput(text="  Hello  ")
        assert obj.text == "Hello"

    def test_non_string_becomes_empty(self):
        obj = LlmOpeningQuestionOutput(text=123)
        assert obj.text == ""


class TestLlmParseModelOutput:
    def test_defaults(self):
        obj = LlmParseModelOutput()
        assert obj.extracted == {}
        assert obj.missing_fields == []
        assert obj.skipped_fields == []
        assert obj.is_complete is False

    def test_extracted_non_dict_becomes_empty(self):
        obj = LlmParseModelOutput(extracted="bad")
        assert obj.extracted == {}

    def test_extracted_filters_by_allowed_keys(self):
        obj = LlmParseModelOutput.model_validate(
            {"extracted": {"location": "Austin", "price": {"min": 100}, "unknown": "x"}},
            context={"allowed_criteria_keys": {"location", "price"}},
        )
        assert "location" in obj.extracted
        assert "price" in obj.extracted
        assert "unknown" not in obj.extracted

    def test_extracted_no_context_keeps_all_keys(self):
        obj = LlmParseModelOutput(extracted={"location": "Austin", "custom": "val"})
        assert "location" in obj.extracted
        assert "custom" in obj.extracted

    def test_missing_fields_non_list_becomes_empty(self):
        obj = LlmParseModelOutput(missing_fields="location")
        assert obj.missing_fields == []

    def test_missing_fields_filters_non_strings(self):
        obj = LlmParseModelOutput(missing_fields=["location", 42, None, "price"])
        assert obj.missing_fields == ["location", "price"]

    def test_next_question_non_dict_becomes_empty_model(self):
        obj = LlmParseModelOutput(next_question="location")
        assert obj.next_question.key is None

    def test_is_complete_non_bool_becomes_false(self):
        obj = LlmParseModelOutput(is_complete="yes")
        assert obj.is_complete is False

    def test_is_complete_true_preserved(self):
        obj = LlmParseModelOutput(is_complete=True)
        assert obj.is_complete is True
