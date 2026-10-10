"""Folding a Google-only user into the email/password user that just confirmed."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from sqlalchemy.exc import OperationalError

from app.services import google_identity
from app.services import google_user_merge as merge

_EMAIL = "jane@example.com"
_OLD_SUB = "11111111-1111-4111-8111-111111111111"
_NEW_SUB = "22222222-2222-4222-8222-222222222222"


def _password_user(status: str = "CONFIRMED") -> dict:
    return {
        "Username": "pw-user",
        "UserStatus": status,
        "Attributes": [{"Name": "email", "Value": _EMAIL}, {"Name": "sub", "Value": _NEW_SUB}],
    }


def _google_user(verified: str | None = "true") -> dict:
    attributes = [
        {"Name": "email", "Value": _EMAIL},
        {"Name": "sub", "Value": _OLD_SUB},
        {"Name": "identities", "Value": '[{"providerName":"Google","userId":"1234567890"}]'},
    ]
    if verified is not None:
        attributes.append({"Name": "email_verified", "Value": verified})
    return {
        "Username": "google_1234567890",
        "UserStatus": "EXTERNAL_PROVIDER",
        "Attributes": attributes,
    }


def _error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "op")


@pytest.fixture
def admin():
    calls: list[tuple[str, dict]] = []
    state = {"users": [_password_user(), _google_user()]}
    fail: dict[str, Exception] = {}

    async def call(operation, **params):
        calls.append((operation, params))
        if operation in fail:
            raise fail[operation]
        if operation == "list_users":
            return {"Users": state["users"]}
        return {}

    with patch.object(google_identity, "call_admin_idp", new=AsyncMock(side_effect=call)):
        yield type("Admin", (), {"calls": calls, "state": state, "fail": fail})


@pytest.fixture
def reassign(admin):
    """The data move, logged in the same call list so its order is visible."""
    with patch.object(google_identity, "reassign_user", new_callable=AsyncMock) as mock:
        mock.side_effect = lambda *args: admin.calls.append(("reassign", {}))
        yield mock


@pytest.fixture
def session(admin):
    """A session whose transaction logs commit or rollback in the same call list."""
    session = MagicMock()
    session.fail_commit = None

    async def exit_(exc_type, exc, tb):
        if exc_type is not None:
            admin.calls.append(("rollback", {}))
        elif session.fail_commit is not None:
            raise session.fail_commit
        else:
            admin.calls.append(("commit", {}))
        return False

    transaction = MagicMock()
    transaction.__aenter__ = AsyncMock(return_value=None)
    transaction.__aexit__ = AsyncMock(side_effect=exit_)
    session.begin.return_value = transaction
    return session


def _ops(admin) -> list[str]:
    return [op for op, _ in admin.calls]


class TestMergeGoogleUser:
    async def test_deletes_links_and_moves_data(self, admin, reassign, session):
        assert await merge.merge_google_user(session, "Jane@Example.com") is True

        # Data first: if it cannot move, the Google user must still exist.
        assert _ops(admin) == [
            "list_users",
            "reassign",
            "admin_delete_user",
            "commit",
            "admin_link_provider_for_user",
        ]
        assert admin.calls[2][1]["Username"] == "google_1234567890"
        assert admin.calls[4][1]["DestinationUser"] == {
            "ProviderName": "Cognito",
            "ProviderAttributeValue": "pw-user",
        }
        assert admin.calls[4][1]["SourceUser"]["ProviderAttributeValue"] == "1234567890"
        reassign.assert_awaited_once_with(session, _OLD_SUB, _NEW_SUB)

    async def test_no_google_user_means_nothing_to_do(self, admin, reassign, session):
        admin.state["users"] = [_password_user()]
        assert await merge.merge_google_user(session, _EMAIL) is False
        assert _ops(admin) == ["list_users"]
        reassign.assert_not_called()

    async def test_unconfirmed_password_user_is_not_merged(self, admin, reassign, session):
        admin.state["users"] = [_password_user(status="UNCONFIRMED"), _google_user()]
        assert await merge.merge_google_user(session, _EMAIL) is False
        assert "admin_delete_user" not in _ops(admin)

    @pytest.mark.parametrize("verified", ["false", None])
    async def test_unverified_google_email_is_never_merged(
        self, admin, reassign, session, verified
    ):
        admin.state["users"] = [_password_user(), _google_user(verified=verified)]
        assert await merge.merge_google_user(session, _EMAIL) is False
        assert "admin_delete_user" not in _ops(admin)
        reassign.assert_not_called()

    async def test_lookup_failure_changes_nothing(self, admin, reassign, session):
        admin.fail["list_users"] = _error("AccessDeniedException")
        assert await merge.merge_google_user(session, _EMAIL) is False
        reassign.assert_not_called()

    async def test_delete_failure_rolls_the_data_move_back(self, admin, reassign, session):
        """Data must never leave a Google user that is still there to sign in as."""
        admin.fail["admin_delete_user"] = _error("AccessDeniedException")
        assert await merge.merge_google_user(session, _EMAIL) is False
        assert _ops(admin)[1:] == ["reassign", "admin_delete_user", "rollback"]

    async def test_commit_failure_after_the_delete_still_links(
        self, admin, reassign, session, caplog
    ):
        """The Google user is gone; linking lets its owner reach the password account."""
        session.fail_commit = OperationalError("commit", {}, Exception("db down"))
        assert await merge.merge_google_user(session, _EMAIL) is True
        assert "admin_link_provider_for_user" in _ops(admin)
        assert "google_merge_commit_failed" in caplog.text

    async def test_link_failure_after_the_delete_still_counts_as_merged(
        self, admin, reassign, session
    ):
        admin.fail["admin_link_provider_for_user"] = _error("InvalidParameterException")
        assert await merge.merge_google_user(session, _EMAIL) is True

    async def test_data_move_failure_leaves_the_google_user_alone(
        self, admin, reassign, session, caplog
    ):
        reassign.side_effect = OperationalError("update", {}, Exception("db down"))
        assert await merge.merge_google_user(session, _EMAIL) is False
        assert _ops(admin)[1:] == ["rollback"]
        assert "google_merge_data_move_failed" in caplog.text

    async def test_email_that_could_break_the_filter_is_refused(self, admin, reassign, session):
        assert await merge.merge_google_user(session, 'x" or email ^= "') is False
        assert admin.calls == []
