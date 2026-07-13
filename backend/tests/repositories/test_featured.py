from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.repositories.featured import list_featured_property_rows

_FIELDS = dict(
    id="p1",
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


def _property_row(property_id: str) -> SimpleNamespace:
    return SimpleNamespace(**{**_FIELDS, "id": property_id})


def _session_with_rows(rows):
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


class TestListFeaturedPropertyRows:
    async def test_returns_empty_list_when_no_properties(self):
        session = _session_with_rows([])
        result = await list_featured_property_rows(session)
        assert result == []

    async def test_returns_at_most_six_rows(self):
        rows = [_property_row(f"p{i}") for i in range(10)]
        session = _session_with_rows(rows)
        result = await list_featured_property_rows(session)
        assert len(result) == 6

    async def test_is_stable_for_the_same_day(self):
        rows = [_property_row(f"p{i}") for i in range(10)]
        session_a = _session_with_rows(rows)
        session_b = _session_with_rows(rows)
        result_a = await list_featured_property_rows(session_a)
        result_b = await list_featured_property_rows(session_b)
        assert [r["id"] for r in result_a] == [r["id"] for r in result_b]

    async def test_maps_rows_to_search_dict_shape(self):
        session = _session_with_rows([_property_row("p1")])
        result = await list_featured_property_rows(session)
        assert result[0]["id"] == "p1"
        assert result[0]["address"] == "100 Main St"
        assert "image" not in result[0]
