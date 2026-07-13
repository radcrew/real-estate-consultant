from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.repositories.properties import (
    get_property_by_id,
    get_property_match_breakdown,
    list_properties_by_broker,
    normalize_criteria,
    search_properties,
)
from app.schemas.search import CriteriaFieldItem

_PROPERTY_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_FIELDS = dict(
    id=_PROPERTY_ID,
    address="100 Main St",
    city="Austin",
    state="TX",
    country="US",
    latitude=30.0,
    longitude=-97.0,
    property_type="Industrial",
    listing_type="PropertyForSale",
    description="A warehouse.",
    size_sqft=10000,
    price=1_000_000,
    rent=None,
    clear_height=24,
    loading_docks=2,
    listing_broker_name="Bob",
    listing_broker_email="bob@example.com",
    listing_broker_phone="555-0100",
)


def _property_row() -> SimpleNamespace:
    return SimpleNamespace(**_FIELDS)


class TestSearchProperties:
    async def test_returns_empty_when_no_matches(self):
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=0)
        rows, total = await search_properties(session, {}, limit=20, offset=0)
        assert rows == []
        assert total == 0
        session.execute.assert_not_called()

    async def test_returns_rows_with_scores_and_total(self):
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=1)
        result = MagicMock()
        result.all.return_value = [(_property_row(), 82.5)]
        session.execute = AsyncMock(return_value=result)

        rows, total = await search_properties(session, {}, limit=20, offset=0)
        assert total == 1
        assert len(rows) == 1
        property_dict, score = rows[0]
        assert property_dict["id"] == _PROPERTY_ID
        assert score == 82.5

    async def test_defaults_null_score_to_zero(self):
        session = AsyncMock()
        session.scalar = AsyncMock(return_value=1)
        result = MagicMock()
        result.all.return_value = [(_property_row(), None)]
        session.execute = AsyncMock(return_value=result)

        rows, _ = await search_properties(session, {}, limit=20, offset=0)
        assert rows[0][1] == 0.0


class TestListPropertiesByBroker:
    async def test_returns_mapped_rows(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [_property_row()]
        session.execute = AsyncMock(return_value=result)

        rows = await list_properties_by_broker(session, "Bob")
        assert rows[0]["listing_broker_name"] == "Bob"

    async def test_returns_empty_list_when_no_match(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=result)

        rows = await list_properties_by_broker(session, "Nobody")
        assert rows == []


class TestGetPropertyById:
    async def test_returns_property_when_found(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = _property_row()
        session.execute = AsyncMock(return_value=result)

        row = await get_property_by_id(session, _PROPERTY_ID)
        assert row["id"] == _PROPERTY_ID

    async def test_returns_none_when_not_found(self):
        session = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)

        row = await get_property_by_id(session, _PROPERTY_ID)
        assert row is None


class TestGetPropertyMatchBreakdown:
    async def test_returns_property_and_score_components(self):
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = (_property_row(), 1.0, 0.8, 0.6, 82.0)
        session.execute = AsyncMock(return_value=result)

        found = await get_property_match_breakdown(session, _PROPERTY_ID, {})
        property_dict, scores = found
        assert property_dict["id"] == _PROPERTY_ID
        assert scores == (1.0, 0.8, 0.6, 82.0)

    async def test_returns_none_when_not_found(self):
        session = AsyncMock()
        result = MagicMock()
        result.first.return_value = None
        session.execute = AsyncMock(return_value=result)

        found = await get_property_match_breakdown(session, _PROPERTY_ID, {})
        assert found is None


class TestNormalizeCriteria:
    async def test_merges_criteria_with_configured_questions(self):
        client = MagicMock()
        metadata = (
            {"price": "range", "location": "location"},
            {"price": "Price", "location": "Location"},
            {"price": "USD", "location": None},
        )
        with patch(
            "app.repositories.properties.list_question_key_metadata",
            new_callable=AsyncMock,
            return_value=metadata,
        ):
            result = await normalize_criteria(client, {"price": {"min": 1000, "max": 2000}})

        assert result["price"] == CriteriaFieldItem(
            type="range", label="Price", unit="USD", data={"min": 1000, "max": 2000},
        )
        assert result["location"] == CriteriaFieldItem(
            type="location", label="Location", unit=None, data=None,
        )

    async def test_includes_unconfigured_criteria_keys_as_unknown(self):
        client = MagicMock()
        with patch(
            "app.repositories.properties.list_question_key_metadata",
            new_callable=AsyncMock,
            return_value=({}, {}, {}),
        ):
            result = await normalize_criteria(client, {"mystery_field": "value"})

        assert result["mystery_field"] == CriteriaFieldItem(
            type="unknown", label="", unit=None, data="value",
        )
