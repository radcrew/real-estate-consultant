import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import (
    CreateIntakeSessionGuidedResponse,
    CreateIntakeSessionLlmResponse,
    GetIntakeSessionResponse,
    IntakeSessionFirstQuestion,
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)

_UID = uuid.uuid4()
_NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)

_FIRST_Q = {
    "key": "location",
    "title": "Location",
    "text": "Where are you looking?",
    "type": "location",
}


class TestIntakeSessionFirstQuestion:
    def test_valid_minimal(self):
        obj = IntakeSessionFirstQuestion(**_FIRST_Q)
        assert obj.key == "location"
        assert obj.options is None

    def test_with_options(self):
        obj = IntakeSessionFirstQuestion(**_FIRST_Q, options=["a", "b"])
        assert obj.options == ["a", "b"]

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            IntakeSessionFirstQuestion(title="T", text="T?", type="text")


class TestCreateIntakeSessionGuidedResponse:
    def test_valid(self):
        obj = CreateIntakeSessionGuidedResponse(
            session_id=_UID,
            status="in_progress",
            current_index=0,
            total_questions=5,
            first_question=_FIRST_Q,
        )
        assert obj.mode == "guided"
        assert obj.current_index == 0
        assert obj.first_question.key == "location"

    def test_mode_is_literal_guided(self):
        obj = CreateIntakeSessionGuidedResponse(
            session_id=_UID,
            status="in_progress",
            current_index=0,
            total_questions=5,
            first_question=_FIRST_Q,
        )
        assert obj.mode == "guided"


class TestCreateIntakeSessionLlmResponse:
    def test_valid(self):
        obj = CreateIntakeSessionLlmResponse(
            session_id=_UID,
            status="in_progress",
            current_index=0,
            total_questions=5,
            message="Tell me what you're looking for.",
            next_question=_FIRST_Q,
        )
        assert obj.mode == "llm"
        assert obj.message == "Tell me what you're looking for."


class TestGetIntakeSessionResponse:
    def test_valid_with_defaults(self):
        obj = GetIntakeSessionResponse(
            current_index=1,
            total_questions=5,
        )
        assert obj.question_history == []
        assert obj.next_question is None

    def test_with_question_history(self):
        obj = GetIntakeSessionResponse(
            current_index=2,
            total_questions=5,
            question_history=[IntakeSessionFirstQuestion(**_FIRST_Q)],
        )
        assert len(obj.question_history) == 1


class TestUpdateIntakeSessionAnswersRequest:
    def test_string_answer(self):
        obj = UpdateIntakeSessionAnswersRequest(key="location", answers="Austin, TX")
        assert obj.key == "location"
        assert obj.answers == "Austin, TX"

    def test_dict_answer(self):
        obj = UpdateIntakeSessionAnswersRequest(key="price", answers={"min": 100000})
        assert obj.answers == {"min": 100000}

    def test_missing_key_raises(self):
        with pytest.raises(ValidationError):
            UpdateIntakeSessionAnswersRequest(answers="Austin")


class TestUpdateIntakeSessionAnswersResponse:
    def test_valid(self):
        session = IntakeSession(id=_UID, status="in_progress")
        obj = UpdateIntakeSessionAnswersResponse(
            session=session,
            current_index=1,
            total_questions=5,
        )
        assert obj.next_question is None
        assert obj.current_index == 1


class TestSubmitLlmIntakeInputRequest:
    def test_valid(self):
        obj = SubmitLlmIntakeInputRequest(input="I need a warehouse in Austin")
        assert obj.input == "I need a warehouse in Austin"

    def test_missing_input_raises(self):
        with pytest.raises(ValidationError):
            SubmitLlmIntakeInputRequest()


class TestSubmitLlmIntakeInputResponse:
    def test_valid(self):
        obj = SubmitLlmIntakeInputResponse(
            extracted={"location": "Austin"},
            criteria={"location": "Austin"},
            current_index=1,
            total_questions=5,
            missing_fields=["price"],
            is_complete=False,
        )
        assert obj.extracted == {"location": "Austin"}
        assert obj.is_complete is False
        assert obj.next_question is None
