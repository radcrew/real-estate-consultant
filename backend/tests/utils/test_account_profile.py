import uuid
from datetime import datetime, timezone

from supabase_auth.types import User

from app.models.profile import Profile
from app.utils.account_profile import account_profile_response

_UUID = str(uuid.uuid4())


def _make_user(email: str = "u@example.com", phone: str | None = None) -> User:
    return User(
        id=_UUID,
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        email=email,
        phone=phone,
    )


class TestAccountProfileResponse:
    def test_profile_none_returns_minimal(self):
        user = _make_user()
        result = account_profile_response(user=user, profile=None)
        assert result.id == _UUID
        assert result.email == "u@example.com"
        assert result.first_name is None
        assert result.last_name is None

    def test_phone_copied_from_user(self):
        user = _make_user(phone="+15550001234")
        result = account_profile_response(user=user, profile=None)
        assert result.phone == "+15550001234"

    def test_profile_fields_merged(self):
        user = _make_user()
        profile = Profile(
            id=_UUID,
            first_name="Alice",
            last_name="Smith",
            city="Austin",
            state="TX",
            country="US",
        )
        result = account_profile_response(user=user, profile=profile)
        assert result.first_name == "Alice"
        assert result.last_name == "Smith"
        assert result.city == "Austin"
        assert result.state == "TX"
        assert result.country == "US"

    def test_avatar_url_from_profile(self):
        user = _make_user()
        profile = Profile(id=_UUID, avatar_url="https://example.com/avatar.png")
        result = account_profile_response(user=user, profile=profile)
        assert result.avatar_url == "https://example.com/avatar.png"

    def test_all_optional_profile_fields_none_by_default(self):
        user = _make_user()
        profile = Profile(id=_UUID)
        result = account_profile_response(user=user, profile=profile)
        for field in ("first_name", "last_name", "address", "city", "state", "zip_code", "country", "avatar_url"):
            assert getattr(result, field) is None, f"{field} should be None"
