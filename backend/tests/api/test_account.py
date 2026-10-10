"""Tests for account profile, password, and saved listings endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

_UID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_SCOPE_ERROR = ClientError(
    {"Error": {"Code": "NotAuthorizedException",
               "Message": "Access Token does not have required scopes"}},
    "GetUser",
)
_PROP_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
_VERIFIED_EMAIL = [
    {"Name": "email", "Value": "user@example.com"},
    {"Name": "email_verified", "Value": "true"},
]


class TestGetAccountProfile:
    async def test_returns_profile(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.profile.get_profile_row",
            new_callable=AsyncMock,
            return_value={
                "id": _UID,
                "email": "user@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
            },
        ):
            r = await client.get("/api/v1/account/profile")
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "user@example.com"
        assert body["first_name"] == "Alice"

    async def test_profile_row_none_returns_minimal(self, client):
        with patch(
            "app.api.v1.endpoints.account.profile.get_profile_row",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.get("/api/v1/account/profile")
        assert r.status_code == 200
        assert r.json()["first_name"] is None

class TestUpdateAccountProfile:
    _AUTH = {"Authorization": "Bearer access-tok"}

    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.update_user_attributes.return_value = {}
        # The user's current, verified email in Cognito.
        idp.get_user.return_value = {"UserAttributes": _VERIFIED_EMAIL}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture
    def profiles(self):
        with (
            patch(
                "app.api.v1.endpoints.account.profile.upsert_profile_patch",
                new_callable=AsyncMock,
            ) as upsert,
            patch(
                "app.api.v1.endpoints.account.profile.get_profile_row",
                new_callable=AsyncMock,
                return_value={"id": _UID, "email": "user@example.com", "first_name": "Bob"},
            ),
        ):
            yield upsert

    @pytest.fixture(autouse=True)
    def cognito_user(self, mock_user):
        mock_user.username = _UID

    @pytest.fixture
    def google_token(self, idp):
        """A Google sign-in token: Cognito refuses GetUser for lack of the admin scope."""
        idp.get_user.side_effect = _SCOPE_ERROR
        with patch(
            "app.api.v1.endpoints.account.profile.call_admin_idp",
            new_callable=AsyncMock,
            return_value={"UserAttributes": _VERIFIED_EMAIL},
        ) as admin:
            yield admin

    async def test_name_change_writes_profile_only(self, client, idp, profiles):
        r = await client.patch("/api/v1/account/profile", json={"first_name": "Bob"})
        assert r.status_code == 200
        assert r.json()["first_name"] == "Bob"
        assert r.json()["email_change_pending"] is False
        assert profiles.call_args.args[2].model_dump(exclude_unset=True) == {"first_name": "Bob"}
        idp.update_user_attributes.assert_not_called()

    async def test_phone_is_written_to_the_profile(self, client, idp, profiles):
        r = await client.patch("/api/v1/account/profile", json={"phone": "+15550001234"})
        assert r.status_code == 200
        assert profiles.call_args.args[2].phone == "+15550001234"
        idp.update_user_attributes.assert_not_called()

    async def test_new_email_goes_to_cognito_not_the_profile(self, client, idp, profiles):
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "new@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 200
        body = r.json()
        assert body["email_change_pending"] is True
        assert body["email"] == "user@example.com"
        idp.update_user_attributes.assert_called_once_with(
            AccessToken="access-tok",
            UserAttributes=[{"Name": "email", "Value": "new@example.com"}],
        )
        # The profile keeps the verified email until the new one is confirmed.
        profiles.assert_not_called()

    async def test_pending_unverified_email_is_not_taken_as_current(self, client, idp, profiles):
        """Cognito may already hold the new address, unverified, while a change is pending."""
        idp.get_user.return_value = {
            "UserAttributes": [
                {"Name": "email", "Value": "new@example.com"},
                {"Name": "email_verified", "Value": "false"},
            ]
        }
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "new@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 200
        assert r.json()["email"] == "user@example.com"
        assert r.json()["email_change_pending"] is True
        profiles.assert_not_called()

    async def test_name_change_makes_no_cognito_call(self, client, idp, profiles, google_token):
        r = await client.patch(
            "/api/v1/account/profile", json={"first_name": "Bob"}, headers=self._AUTH
        )
        assert r.status_code == 200
        assert profiles.call_args.args[2].model_dump(exclude_unset=True) == {"first_name": "Bob"}
        idp.get_user.assert_not_called()
        google_token.assert_not_called()

    async def test_google_token_reads_the_email_through_the_admin_api(
        self, client, idp, profiles, google_token
    ):
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "user@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 200
        assert r.json()["email_change_pending"] is False
        google_token.assert_awaited_once()
        assert google_token.await_args.kwargs["Username"] == _UID

    async def test_google_token_save_still_works_without_admin_access(
        self, client, idp, profiles, google_token
    ):
        google_token.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "no"}}, "AdminGetUser"
        )
        r = await client.patch(
            "/api/v1/account/profile",
            json={"email": "user@example.com", "first_name": "Bob"},
            headers=self._AUTH,
        )
        assert r.status_code == 200
        assert r.json()["email_change_pending"] is False
        assert profiles.call_args.args[2].model_dump(exclude_unset=True) == {"first_name": "Bob"}

    async def test_google_token_cannot_change_the_email(self, client, idp, profiles, google_token):
        idp.update_user_attributes.side_effect = _SCOPE_ERROR
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "new@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 400
        assert "sign in with your email and password" in r.json()["detail"]

    async def test_email_differing_only_in_case_is_not_a_change(self, client, idp, profiles):
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "User@Example.com"}, headers=self._AUTH
        )
        assert r.json()["email_change_pending"] is False
        idp.update_user_attributes.assert_not_called()

    async def test_unchanged_email_is_ignored(self, client, idp, profiles):
        r = await client.patch(
            "/api/v1/account/profile",
            json={"email": "user@example.com", "first_name": "Bob"},
            headers=self._AUTH,
        )
        assert r.status_code == 200
        assert r.json()["email_change_pending"] is False
        idp.update_user_attributes.assert_not_called()

    async def test_email_taken_returns_409(self, client, idp, profiles):
        idp.update_user_attributes.side_effect = ClientError(
            {"Error": {"Code": "AliasExistsException", "Message": "taken"}},
            "UpdateUserAttributes",
        )
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "new@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 409

    async def test_google_user_cannot_change_email(self, client, idp, profiles, mock_user):
        mock_user.username = "google_1234"
        r = await client.patch(
            "/api/v1/account/profile", json={"email": "new@example.com"}, headers=self._AUTH
        )
        assert r.status_code == 400
        idp.update_user_attributes.assert_not_called()

    async def test_api_key_caller_cannot_change_email(self, client, idp, profiles, mock_user):
        mock_user.username = None
        r = await client.patch(
            "/api/v1/account/profile",
            json={"email": "new@example.com"},
            headers={"X-API-Key": "rad_abcdefghijklmnop"},
        )
        assert r.status_code == 403
        idp.update_user_attributes.assert_not_called()

    async def test_empty_body_returns_400(self, client):
        r = await client.patch("/api/v1/account/profile", json={})
        assert r.status_code == 400


class TestVerifyAccountEmail:
    _AUTH = {"Authorization": "Bearer access-tok"}

    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.verify_user_attribute.return_value = {}
        idp.get_user.return_value = {
            "UserAttributes": [{"Name": "email", "Value": "new@example.com"}]
        }
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture
    def profiles(self):
        with (
            patch(
                "app.api.v1.endpoints.account.profile.upsert_profile_patch",
                new_callable=AsyncMock,
            ) as upsert,
            patch(
                "app.api.v1.endpoints.account.profile.get_profile_row",
                new_callable=AsyncMock,
                return_value={"id": _UID, "email": "new@example.com"},
            ),
        ):
            yield upsert

    @pytest.fixture(autouse=True)
    def cognito_user(self, mock_user):
        mock_user.username = _UID

    async def test_verified_email_is_written_to_the_profile(self, client, idp, profiles):
        r = await client.post(
            "/api/v1/account/email/verify", json={"code": " 123456 "}, headers=self._AUTH
        )
        assert r.status_code == 200
        assert r.json()["email"] == "new@example.com"
        idp.verify_user_attribute.assert_called_once_with(
            AccessToken="access-tok", AttributeName="email", Code="123456"
        )
        assert profiles.call_args.args[2].email == "new@example.com"

    async def test_wrong_code_returns_400_and_keeps_the_profile(self, client, idp, profiles):
        idp.verify_user_attribute.side_effect = ClientError(
            {"Error": {"Code": "CodeMismatchException", "Message": "bad"}}, "VerifyUserAttribute"
        )
        r = await client.post(
            "/api/v1/account/email/verify", json={"code": "000000"}, headers=self._AUTH
        )
        assert r.status_code == 400
        profiles.assert_not_called()

    async def test_api_key_caller_returns_403(self, client, idp, profiles, mock_user):
        mock_user.username = None
        r = await client.post(
            "/api/v1/account/email/verify",
            json={"code": "123456"},
            headers={"X-API-Key": "rad_abcdefghijklmnop"},
        )
        assert r.status_code == 403


class TestChangePassword:
    _BODY = {"current_password": "oldpass11", "new_password": "newpass11"}
    _AUTH = {"Authorization": "Bearer access-tok"}

    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.change_password.return_value = {}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture(autouse=True)
    def cognito_user(self, mock_user):
        mock_user.username = _UID

    async def test_success_returns_204(self, client, idp):
        r = await client.post("/api/v1/account/password", json=self._BODY, headers=self._AUTH)
        assert r.status_code == 204
        idp.change_password.assert_called_once_with(
            PreviousPassword="oldpass11", ProposedPassword="newpass11", AccessToken="access-tok"
        )

    async def test_wrong_current_password_returns_401(self, client, idp):
        idp.change_password.side_effect = ClientError(
            {"Error": {"Code": "NotAuthorizedException", "Message": "Incorrect"}}, "ChangePassword"
        )
        r = await client.post("/api/v1/account/password", json=self._BODY, headers=self._AUTH)
        assert r.status_code == 401
        assert r.json()["detail"] == "Current password is incorrect."

    async def test_weak_new_password_returns_422(self, client, idp):
        idp.change_password.side_effect = ClientError(
            {"Error": {"Code": "InvalidPasswordException", "Message": "Needs a number"}},
            "ChangePassword",
        )
        r = await client.post("/api/v1/account/password", json=self._BODY, headers=self._AUTH)
        assert r.status_code == 422

    async def test_same_password_returns_422(self, client, idp):
        r = await client.post(
            "/api/v1/account/password",
            json={"current_password": "samepass1", "new_password": "samepass1"},
            headers=self._AUTH,
        )
        assert r.status_code == 422
        idp.change_password.assert_not_called()

    async def test_google_user_returns_400(self, client, idp, mock_user):
        mock_user.username = "google_1234"
        r = await client.post("/api/v1/account/password", json=self._BODY, headers=self._AUTH)
        assert r.status_code == 400
        idp.change_password.assert_not_called()

    async def test_api_key_caller_returns_403(self, client, idp, mock_user):
        mock_user.username = None
        r = await client.post(
            "/api/v1/account/password",
            json=self._BODY,
            headers={"X-API-Key": "rad_abcdefghijklmnop"},
        )
        assert r.status_code == 403
        idp.change_password.assert_not_called()


class TestSavedListings:
    async def test_get_saved_returns_ids(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.list_saved_property_ids",
            new_callable=AsyncMock,
            return_value=[_PROP_UUID],
        ):
            r = await client.get("/api/v1/account/saved")
        assert r.status_code == 200
        assert r.json()["property_ids"] == [_PROP_UUID]

    async def test_save_listing_returns_204(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.add_saved_listing",
            new_callable=AsyncMock,
        ):
            r = await client.post("/api/v1/account/saved", json={"property_id": _PROP_UUID})
        assert r.status_code == 204

    async def test_unsave_listing_returns_204(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.remove_saved_listing",
            new_callable=AsyncMock,
        ):
            r = await client.delete(f"/api/v1/account/saved/{_PROP_UUID}")
        assert r.status_code == 204
