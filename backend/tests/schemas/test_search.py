import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.search import (
    CriteriaFieldItem,
    PropertyMatch,
    QuickSearchBody,
    SearchCriteriaUpdateResponse,
    SearchPropertiesResponse,
    UpdateSearchCriteriaBody,
)


class TestQuickSearchBody:
    def test_all_optional(self):
        obj = QuickSearchBody()
        assert obj.location is None
        assert obj.property_types == []
        assert obj.price_min is None

    def test_with_values(self):
        obj = QuickSearchBody(
            location="Austin, TX",
            property_types=["industrial"],
            price_min=100_000,
            price_max=500_000,
        )
        assert obj.location == "Austin, TX"
        assert obj.property_types == ["industrial"]
        assert obj.price_max == 500_000


class TestUpdateSearchCriteriaBody:
    def test_accepts_arbitrary_dict(self):
        obj = UpdateSearchCriteriaBody({"location": "Austin", "price": {"min": 100}})
        assert obj.root["location"] == "Austin"

    def test_empty_dict_valid(self):
        obj = UpdateSearchCriteriaBody({})
        assert obj.root == {}


class TestCriteriaFieldItem:
    def test_required_fields(self):
        obj = CriteriaFieldItem(type="range", label="Price", unit="USD", data=None)
        assert obj.type == "range"
        assert obj.unit == "USD"
        assert obj.data is None

    def test_data_can_be_any_type(self):
        obj = CriteriaFieldItem(type="range", label="Size", unit="sqft", data={"min": 1000})
        assert obj.data == {"min": 1000}

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            CriteriaFieldItem(label="Price", unit=None, data=None)


class TestSearchCriteriaUpdateResponse:
    def test_defaults(self):
        obj = SearchCriteriaUpdateResponse()
        assert obj.status == "in_progress"
        assert obj.criteria == {}
        assert obj.id is None

    def test_with_uuid_and_criteria(self):
        uid = uuid.uuid4()
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        obj = SearchCriteriaUpdateResponse(
            id=uid,
            status="complete",
            created_at=now,
            search_profile_id=uid,
            criteria={
                "location": CriteriaFieldItem(type="location", label="Location", unit=None, data="Austin")
            },
        )
        assert obj.id == uid
        assert obj.criteria["location"].data == "Austin"
