import pytest
from pydantic import ValidationError

from app.schemas.listings import (
    ListingSubmissionCreate,
    ListingSubmissionStatusUpdate,
)


VALID_PAYLOAD = {
    "property_type": "Industrial",
    "listing_type": "ForSale",
    "title": "Warehouse on Main",
    "city": "Austin",
    "state": "TX",
    "contact_name": "Alice",
    "contact_email": "alice@example.com",
}


class TestListingSubmissionCreate:
    def test_valid_minimal_payload(self):
        obj = ListingSubmissionCreate(**VALID_PAYLOAD)
        assert obj.title == "Warehouse on Main"
        assert obj.description is None
        assert obj.image_urls == []

    def test_optional_numeric_fields(self):
        obj = ListingSubmissionCreate(
            **VALID_PAYLOAD,
            size_sqft=10000,
            price=1_500_000,
            clear_height=32.0,
            loading_docks=4,
        )
        assert obj.size_sqft == 10000
        assert obj.loading_docks == 4

    def test_whitespace_stripped(self):
        obj = ListingSubmissionCreate(**{**VALID_PAYLOAD, "city": "  Austin  "})
        assert obj.city == "Austin"

    def test_missing_required_field_raises(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "city"}
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(**payload)

    def test_empty_title_raises(self):
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(**{**VALID_PAYLOAD, "title": ""})

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(**{**VALID_PAYLOAD, "contact_email": "not-an-email"})

    def test_negative_price_raises(self):
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(**{**VALID_PAYLOAD, "price": -100})

    def test_negative_loading_docks_raises(self):
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(**{**VALID_PAYLOAD, "loading_docks": -1})

    def test_image_urls_max_length(self):
        with pytest.raises(ValidationError):
            ListingSubmissionCreate(
                **VALID_PAYLOAD,
                image_urls=["https://x.com/img.png"] * 11,
            )


class TestListingSubmissionStatusUpdate:
    def test_valid_statuses(self):
        for status in ("pending", "approved", "rejected"):
            obj = ListingSubmissionStatusUpdate(status=status)
            assert obj.status == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            ListingSubmissionStatusUpdate(status="unknown")
