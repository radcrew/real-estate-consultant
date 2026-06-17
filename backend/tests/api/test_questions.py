"""Tests for POST /api/v1/questions (protected)."""
from unittest.mock import AsyncMock, patch

import pytest

_Q_ROW = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "key": "location",
    "text": "Where are you looking?",
    "type": "location",
    "order_index": 0,
    "required": False,
    "options": None,
}


class TestCreateQuestion:
    async def test_success_returns_201(self, client):
        with patch(
            "app.api.v1.endpoints.questions.router.insert_question_row",
            new_callable=AsyncMock,
            return_value=_Q_ROW,
        ):
            r = await client.post(
                "/api/v1/questions",
                json={"text": "Where?", "type": "location", "order_index": 0, "key": "location"},
            )
        assert r.status_code == 201
        body = r.json()
        assert body["key"] == "location"
        assert body["type"] == "location"

    async def test_missing_key_returns_422(self, client):
        r = await client.post(
            "/api/v1/questions",
            json={"text": "Where?", "order_index": 0},
        )
        assert r.status_code == 422

    async def test_default_type_is_text(self, client):
        with patch(
            "app.api.v1.endpoints.questions.router.insert_question_row",
            new_callable=AsyncMock,
            return_value={**_Q_ROW, "type": "text"},
        ):
            r = await client.post(
                "/api/v1/questions",
                json={"text": "Notes?", "order_index": 1, "key": "notes"},
            )
        assert r.status_code == 201
        assert r.json()["type"] == "text"
