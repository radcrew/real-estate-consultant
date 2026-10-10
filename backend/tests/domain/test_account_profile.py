import uuid

from app.domain.account_profile import account_profile_response
from app.models.auth_user import AuthUser
from app.models.profile import Profile

_UUID = str(uuid.uuid4())


def _make_user() -> AuthUser:
    return AuthUser(id=_UUID)


class TestAccountProfileResponse:
    def test_profile_none_returns_only_the_id(self):
        result = account_profile_response(user=_make_user(), profile=None)
        assert result.id == _UUID
        assert result.email is None
        assert result.phone is None
        assert result.first_name is None

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

    def test_email_and_phone_come_from_the_profile_row(self):
        user = _make_user()
        profile = Profile(id=_UUID, email="row@example.com", phone="+15550001234")
        result = account_profile_response(user=user, profile=profile)
        assert result.email == "row@example.com"
        assert result.phone == "+15550001234"

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
