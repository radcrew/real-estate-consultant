"""Tests for Pydantic models — Properties and PropertyImages."""
import pytest
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.models.properties import Properties
from app.models.property_images import PropertyImages


class TestProperties:
    def test_all_fields_optional(self):
        p = Properties()
        assert p.address is None
        assert p.city is None

    def test_valid_uuid_accepted(self):
        uid = uuid4()
        p = Properties(id=uid)
        assert p.id == uid

    def test_string_values_stripped(self):
        p = Properties(address="  123 Main St  ", city="  Austin  ")
        assert p.address == "123 Main St"
        assert p.city == "Austin"

    def test_numeric_fields(self):
        p = Properties(latitude=30.5, longitude=-97.7, size_sqft=10000.0, price=500000.0)
        assert p.latitude == 30.5
        assert p.size_sqft == 10000.0

    def test_all_fields_populated(self):
        uid = uuid4()
        p = Properties(
            id=uid,
            address="100 Commerce St",
            city="Dallas",
            state="TX",
            country="US",
            property_type="Industrial",
            listing_type="Sale",
            size_sqft=50000.0,
            price=2500000.0,
            listing_broker_name="John Doe",
        )
        assert p.city == "Dallas"
        assert p.listing_broker_name == "John Doe"


class TestPropertyImages:
    def test_valid_model(self):
        uid = uuid4()
        img = PropertyImages(property_id=uid, url="https://example.com/img.jpg")
        assert img.property_id == uid
        assert img.url == "https://example.com/img.jpg"

    def test_missing_property_id_raises(self):
        with pytest.raises(ValidationError):
            PropertyImages(url="https://example.com/img.jpg")

    def test_missing_url_raises(self):
        with pytest.raises(ValidationError):
            PropertyImages(property_id=uuid4())

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            PropertyImages(property_id="not-a-uuid", url="https://example.com/img.jpg")
