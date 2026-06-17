import pytest
from pydantic import ValidationError

from app.schemas.account import (
    AccountPasswordChangeRequest,
    AccountProfileResponse,
    AccountProfileUpdate,
    SavedListingCreate,
)


class TestAccountProfileUpdate:
    def test_all_fields_optional(self):
        obj = AccountProfileUpdate()
        assert obj.email is None
        assert obj.first_name is None

    def test_valid_partial_update(self):
        obj = AccountProfileUpdate(first_name="Alice", city="Austin")
        assert obj.first_name == "Alice"
        assert obj.city == "Austin"

    def test_email_must_be_valid(self):
        with pytest.raises(ValidationError):
            AccountProfileUpdate(email="not-an-email")

    def test_first_name_max_length(self):
        with pytest.raises(ValidationError):
            AccountProfileUpdate(first_name="A" * 121)

    def test_zip_code_max_length(self):
        with pytest.raises(ValidationError):
            AccountProfileUpdate(zip_code="Z" * 33)


class TestAccountPasswordChangeRequest:
    def test_valid(self):
        obj = AccountPasswordChangeRequest(
            current_password="old-pass",
            new_password="new-secure-pass",
        )
        assert obj.new_password == "new-secure-pass"

    def test_new_password_too_short(self):
        with pytest.raises(ValidationError):
            AccountPasswordChangeRequest(
                current_password="old",
                new_password="short",
            )

    def test_current_password_empty_raises(self):
        with pytest.raises(ValidationError):
            AccountPasswordChangeRequest(current_password="", new_password="validpass")

    def test_new_password_max_length(self):
        with pytest.raises(ValidationError):
            AccountPasswordChangeRequest(
                current_password="old",
                new_password="A" * 73,
            )


class TestAccountProfileResponse:
    def test_all_optional_except_id(self):
        obj = AccountProfileResponse(id="u1", email=None)
        assert obj.id == "u1"
        assert obj.email is None
        assert obj.first_name is None

    def test_full_profile(self):
        obj = AccountProfileResponse(
            id="u1",
            email="u@example.com",
            first_name="Bob",
            last_name="Jones",
            city="Dallas",
            state="TX",
            country="US",
        )
        assert obj.last_name == "Jones"
        assert obj.country == "US"


class TestSavedListingCreate:
    def test_valid_uuid(self):
        obj = SavedListingCreate(property_id="a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert str(obj.property_id) == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            SavedListingCreate(property_id="not-a-uuid")
