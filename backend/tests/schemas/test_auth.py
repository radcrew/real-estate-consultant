from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    EmailPasswordRequest,
    SignInRequest,
    SignInResponse,
    SignInUser,
    SignUpRequest,
    SignUpResponse,
)


class TestEmailPasswordRequest:
    def test_valid(self):
        obj = EmailPasswordRequest(email="user@example.com", password="securepass")
        assert obj.email == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            EmailPasswordRequest(email="not-email", password="securepass")

    def test_password_too_short_raises(self):
        with pytest.raises(ValidationError):
            EmailPasswordRequest(email="u@example.com", password="short")

    def test_password_too_long_raises(self):
        with pytest.raises(ValidationError):
            EmailPasswordRequest(email="u@example.com", password="A" * 73)


class TestSignUpRequest:
    def test_valid(self):
        obj = SignUpRequest(
            email="u@example.com",
            password="securepass",
            first_name="Alice",
            last_name="Smith",
        )
        assert obj.first_name == "Alice"

    def test_empty_first_name_raises(self):
        with pytest.raises(ValidationError):
            SignUpRequest(
                email="u@example.com",
                password="securepass",
                first_name="",
                last_name="Smith",
            )

    def test_first_name_too_long_raises(self):
        with pytest.raises(ValidationError):
            SignUpRequest(
                email="u@example.com",
                password="securepass",
                first_name="A" * 121,
                last_name="Smith",
            )


class TestSignInRequest:
    def test_valid(self):
        obj = SignInRequest(email="u@example.com", password="securepass")
        assert obj.email == "u@example.com"


class TestSignInResponse:
    def test_valid(self):
        user = SignInUser(id="u1", email="u@example.com")
        obj = SignInResponse(
            access_token="tok",
            refresh_token="ref",
            expires_in=3600,
            token_type="bearer",
            user=user,
        )
        assert obj.token_type == "bearer"
        assert obj.user.id == "u1"


class TestSignUpResponse:
    def test_valid(self):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        obj = SignUpResponse(id="u1", email="u@example.com", created_at=now)
        assert obj.id == "u1"

    def test_email_can_be_none(self):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        obj = SignUpResponse(id="u1", email=None, created_at=now)
        assert obj.email is None
