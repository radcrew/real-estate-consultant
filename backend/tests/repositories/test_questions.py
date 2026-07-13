import pytest
from fastapi import HTTPException

from app.repositories.questions import (
    insert_question_row,
    list_intake_questions,
    list_question_key_metadata,
    map_question_to_model,
    next_question_row_after_order,
    order_for_question_key,
    sorted_intake_questions,
)
from tests.repositories.conftest import make_supabase_client

_PRICE_QUESTION = {
    "key": "price",
    "title": "Price",
    "text": "What's your budget?",
    "type": "range",
    "options": {"unit": "USD"},
    "order_index": 2,
}
_LOCATION_QUESTION = {
    "key": "location",
    "title": "Location",
    "text": "Where?",
    "type": "location",
    "options": None,
    "order_index": 1,
}


class TestMapQuestionToModel:
    def test_maps_valid_row(self):
        model = map_question_to_model(_LOCATION_QUESTION)
        assert model.key == "location"
        assert model.text == "Where?"

    def test_raises_502_when_key_missing(self):
        with pytest.raises(HTTPException) as info:
            map_question_to_model({"text": "x", "type": "text"})
        assert info.value.status_code == 502

    def test_raises_502_when_text_not_a_string(self):
        with pytest.raises(HTTPException) as info:
            map_question_to_model({"key": "price", "text": None, "type": "range"})
        assert info.value.status_code == 502


class TestOrderForQuestionKey:
    def test_returns_order_index_for_matching_key(self):
        result = order_for_question_key([_PRICE_QUESTION, _LOCATION_QUESTION], "price")
        assert result == 2

    def test_returns_none_for_unknown_key(self):
        result = order_for_question_key([_PRICE_QUESTION], "unknown")
        assert result is None


class TestSortedIntakeQuestions:
    def test_sorts_by_order_index(self):
        result = sorted_intake_questions([_PRICE_QUESTION, _LOCATION_QUESTION])
        assert [q["key"] for q in result] == ["location", "price"]

    def test_treats_missing_order_index_as_zero(self):
        no_order = {"key": "x", "order_index": None}
        result = sorted_intake_questions([_PRICE_QUESTION, no_order])
        assert result[0]["key"] == "x"


class TestNextQuestionRowAfterOrder:
    def test_returns_first_row_after_given_order(self):
        result = next_question_row_after_order(
            [_LOCATION_QUESTION, _PRICE_QUESTION],
            after_order=1,
        )
        assert result["key"] == "price"

    def test_returns_none_when_no_row_after_order(self):
        result = next_question_row_after_order([_PRICE_QUESTION], after_order=2)
        assert result is None


class TestListQuestionKeyMetadata:
    async def test_builds_types_titles_and_units(self):
        client = make_supabase_client([_PRICE_QUESTION, _LOCATION_QUESTION])
        types, titles, units = await list_question_key_metadata(client)
        assert types == {"price": "range", "location": "location"}
        assert titles == {"price": "Price", "location": "Location"}
        assert units == {"price": "USD", "location": None}

    async def test_skips_rows_with_invalid_keys(self):
        client = make_supabase_client([{"key": None, "type": "text", "title": "x"}])
        types, titles, units = await list_question_key_metadata(client)
        assert types == {}
        assert titles == {}
        assert units == {}


class TestListIntakeQuestions:
    async def test_returns_questions(self):
        client = make_supabase_client([_PRICE_QUESTION])
        result = await list_intake_questions(client)
        assert result == [_PRICE_QUESTION]

    async def test_raises_502_when_no_questions_configured(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await list_intake_questions(client)
        assert info.value.status_code == 502


class TestInsertQuestionRow:
    async def test_returns_inserted_row(self):
        client = make_supabase_client([_PRICE_QUESTION])
        result = await insert_question_row(client, {"key": "price"})
        assert result == _PRICE_QUESTION

    async def test_raises_502_on_empty_response(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await insert_question_row(client, {"key": "price"})
        assert info.value.status_code == 502
