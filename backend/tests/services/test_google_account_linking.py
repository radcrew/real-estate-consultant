"""Folding a first-time Google sign-in into an existing email/password account."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import ClientError

from app.services import google_account_linking as linking

_EMAIL = "jane@example.com"
_CLAIMS = {
    "cognito:username": "google_1234567890",
    "email": "Jane@Example.com",
    "email_verified": "true",
    "identities": '[{"providerName": "Google", "userId": "1234567890"}]',
}


def _user(username: str, *, status: str = "CONFIRMED", verified: str = "true") -> dict:
    return {
        "Username": username,
        "UserStatus": status,
        "Enabled": True,
        "Attributes": [
            {"Name": "email", "Value": _EMAIL},
            {"Name": "email_verified", "Value": verified},
        ],
    }


def _error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "op")


@pytest.fixture
def admin():
    """Fake admin calls; list_users answers with ``admin.users``."""
    calls: list[tuple[str, dict]] = []
    state = {"users": [_user("google_1234567890", status="EXTERNAL_PROVIDER"), _user("pw-user")]}
    fail: dict[str, Exception] = {}

    async def call(operation, **params):
        calls.append((operation, params))
        if operation in fail:
            raise fail[operation]
        if operation == "list_users":
            return {"Users": state["users"]}
        return {}

    with patch.object(linking, "call_admin_idp", new=AsyncMock(side_effect=call)):
        yield type("Admin", (), {"calls": calls, "state": state, "fail": fail})


def _ops(admin) -> list[str]:
    return [op for op, _ in admin.calls]


class TestLinkToExistingAccount:
    async def test_links_to_the_password_account_with_the_same_email(self, admin):
        assert await linking.link_to_existing_account(_CLAIMS) is True

        assert _ops(admin) == ["list_users", "admin_delete_user", "admin_link_provider_for_user"]
        assert admin.calls[0][1]["Filter"] == 'email = "jane@example.com"'
        assert admin.calls[1][1]["Username"] == "google_1234567890"
        assert admin.calls[2][1]["DestinationUser"] == {
            "ProviderName": "Cognito",
            "ProviderAttributeValue": "pw-user",
        }
        assert admin.calls[2][1]["SourceUser"] == {
            "ProviderName": "Google",
            "ProviderAttributeName": "Cognito_Subject",
            "ProviderAttributeValue": "1234567890",
        }

    async def test_nothing_to_do_without_a_password_account(self, admin):
        admin.state["users"] = [_user("google_1234567890", status="EXTERNAL_PROVIDER")]
        assert await linking.link_to_existing_account(_CLAIMS) is False
        assert _ops(admin) == ["list_users"]

    async def test_already_linked_user_is_left_alone(self, admin):
        """A linked sign-in comes back as the password user, not a google_ user."""
        claims = {**_CLAIMS, "cognito:username": "pw-user"}
        assert await linking.link_to_existing_account(claims) is False
        assert admin.calls == []

    @pytest.mark.parametrize("verified", ["false", None])
    async def test_unverified_google_email_is_never_linked(self, admin, verified):
        claims = {**_CLAIMS, "email_verified": verified}
        assert await linking.link_to_existing_account(claims) is False
        assert admin.calls == []

    async def test_unverified_password_account_is_never_linked(self, admin):
        admin.state["users"] = [_user("pw-user", verified="false")]
        assert await linking.link_to_existing_account(_CLAIMS) is False
        assert "admin_delete_user" not in _ops(admin)

    async def test_two_password_accounts_is_ambiguous(self, admin):
        admin.state["users"] = [_user("pw-a"), _user("pw-b")]
        assert await linking.link_to_existing_account(_CLAIMS) is False
        assert "admin_delete_user" not in _ops(admin)

    async def test_email_that_could_break_the_filter_is_refused(self, admin):
        claims = {**_CLAIMS, "email": 'x" or email ^= "'}
        assert await linking.link_to_existing_account(claims) is False
        assert admin.calls == []

    async def test_lookup_failure_lets_sign_in_continue(self, admin):
        admin.fail["list_users"] = _error("AccessDeniedException")
        assert await linking.link_to_existing_account(_CLAIMS) is False

    async def test_delete_failure_lets_sign_in_continue(self, admin):
        admin.fail["admin_delete_user"] = _error("AccessDeniedException")
        assert await linking.link_to_existing_account(_CLAIMS) is False
        assert "admin_link_provider_for_user" not in _ops(admin)

    async def test_link_failure_after_delete_still_asks_for_a_retry(self, admin):
        """The tokens belong to the deleted user, so they must not be handed out."""
        admin.fail["admin_link_provider_for_user"] = _error("InvalidParameterException")
        assert await linking.link_to_existing_account(_CLAIMS) is True

    async def test_identities_as_a_list_are_read_too(self, admin):
        claims = {**_CLAIMS, "identities": [{"providerName": "Google", "userId": "999"}]}
        assert await linking.link_to_existing_account(claims) is True
        assert admin.calls[2][1]["SourceUser"]["ProviderAttributeValue"] == "999"
