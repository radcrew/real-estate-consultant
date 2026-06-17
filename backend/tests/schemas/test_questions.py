import pytest
from pydantic import ValidationError

from app.schemas.questions import CreateQuestionRequest


class TestCreateQuestionRequest:
    def test_valid_minimal(self):
        obj = CreateQuestionRequest(text="Where?", order_index=0, key="location")
        assert obj.question_type == "text"
        assert obj.required is False
        assert obj.options is None

    def test_type_alias_accepted(self):
        obj = CreateQuestionRequest.model_validate({
            "text": "What type?",
            "type": "multiselect",
            "order_index": 1,
            "key": "property_type",
        })
        assert obj.question_type == "multiselect"

    def test_whitespace_stripped(self):
        obj = CreateQuestionRequest(text="  Where?  ", order_index=0, key="  location  ")
        assert obj.text == "Where?"
        assert obj.key == "location"

    def test_options_can_be_list(self):
        obj = CreateQuestionRequest(
            text="What?",
            order_index=0,
            key="type",
            options=["office", "industrial"],
        )
        assert obj.options == ["office", "industrial"]

    def test_missing_text_raises(self):
        with pytest.raises(ValidationError):
            CreateQuestionRequest(order_index=0, key="location")
