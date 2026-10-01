"""Tests for the public /api/v1/auth endpoints."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import jwt
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

_NEW_SUB = "6f1c2a9e-0000-4000-8000-000000000002"


def _client_error(code: str, message: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "SignUp")


_SIGN_IN = {"email": "user@example.com", "password": "securepass"}
_SIGN_UP = {
    "email": "new@example.com",
    "password": "securepass",
    "first_name": "Alice",
    "last_name": "Smith",
}


_AUTH_RESULT = {
    "AccessToken": "access-tok",
    "IdToken": "id-tok",
    "RefreshToken": "refresh-tok",
    "ExpiresIn": 3600,
    "TokenType": "Bearer",
}


class TestSignIn:
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.initiate_auth.return_value = {"AuthenticationResult": dict(_AUTH_RESULT)}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture(autouse=True)
    def verify(self):
        claims = {"sub": _NEW_SUB, "username": _NEW_SUB}
        with patch(
            "app.api.v1.endpoints.auth.sign_in.verify_access_token", return_value=claims
        ) as mock:
            yield mock

    async def test_success_returns_cognito_session(self, client, idp):
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 200
        assert r.json() == {
            "access_token": "access-tok",
            "id_token": "id-tok",
            "refresh_token": "refresh-tok",
            "expires_in": 3600,
            "token_type": "Bearer",
            "user": {"id": _NEW_SUB, "email": "user@example.com", "username": _NEW_SUB},
        }

    async def test_uses_password_flow_with_secret_hash(self, client, idp):
        await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        kwargs = idp.initiate_auth.call_args.kwargs
        assert kwargs["AuthFlow"] == "USER_PASSWORD_AUTH"
        assert kwargs["AuthParameters"]["USERNAME"] == "user@example.com"
        assert kwargs["AuthParameters"]["SECRET_HASH"]

    @pytest.mark.parametrize("code", ["NotAuthorizedException", "UserNotFoundException"])
    async def test_bad_credentials_and_unknown_user_look_the_same(self, client, idp, code):
        idp.initiate_auth.side_effect = _client_error(code, "nope")
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid email or password."

    async def test_unconfirmed_user_returns_403(self, client, idp):
        idp.initiate_auth.side_effect = _client_error("UserNotConfirmedException", "confirm")
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 403
        assert "Confirm your email" in r.json()["detail"]

    async def test_challenge_returns_403(self, client, idp):
        idp.initiate_auth.return_value = {"ChallengeName": "NEW_PASSWORD_REQUIRED"}
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 403
        assert "NEW_PASSWORD_REQUIRED" in r.json()["detail"]

    async def test_unreachable_cognito_returns_503(self, client, idp):
        idp.initiate_auth.side_effect = EndpointConnectionError(endpoint_url="https://cognito-idp")
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 503

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/auth/sign-in", json={"email": "bad"})
        assert r.status_code == 422


class TestSignUp:
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.sign_up.return_value = {"UserSub": _NEW_SUB, "UserConfirmed": False}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture
    def upsert(self):
        with patch(
            "app.api.v1.endpoints.auth.sign_up.upsert_profile_patch",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    async def test_success_returns_201_and_needs_confirmation(self, client, idp, upsert):
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 201
        assert r.json() == {
            "id": _NEW_SUB,
            "email": "new@example.com",
            "confirmation_required": True,
        }

    async def test_sends_names_as_cognito_attributes(self, client, idp, upsert):
        await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        kwargs = idp.sign_up.call_args.kwargs
        assert kwargs["Username"] == "new@example.com"
        assert {"Name": "given_name", "Value": "Alice"} in kwargs["UserAttributes"]
        assert {"Name": "family_name", "Value": "Smith"} in kwargs["UserAttributes"]
        assert kwargs["SecretHash"]

    async def test_profile_row_is_keyed_by_cognito_sub(self, client, idp, upsert):
        await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        user_id, patch_body = upsert.call_args.args[1:]
        assert str(user_id) == _NEW_SUB
        assert patch_body.first_name == "Alice"
        assert patch_body.email == "new@example.com"

    async def test_email_already_exists_returns_409(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error("UsernameExistsException", "exists")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 409
        upsert.assert_not_called()

    async def test_weak_password_returns_422_with_cognito_message(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error(
            "InvalidPasswordException", "Password must have uppercase characters"
        )
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 422
        assert "uppercase" in r.json()["detail"]

    async def test_throttled_returns_429(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error("TooManyRequestsException", "slow down")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 429

    async def test_unreachable_cognito_returns_503(self, client, idp, upsert):
        idp.sign_up.side_effect = EndpointConnectionError(endpoint_url="https://cognito-idp")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 503

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/auth/sign-up", json={"email": "x@x.com", "password": "pass"})
        assert r.status_code == 422


class TestConfirmSignUp:
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.confirm_sign_up.return_value = {}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    async def test_valid_code_returns_204(self, client, idp):
        r = await client.post(
            "/api/v1/auth/confirm", json={"email": "new@example.com", "code": " 123456 "}
        )
        assert r.status_code == 204
        kwargs = idp.confirm_sign_up.call_args.kwargs
        assert kwargs["Username"] == "new@example.com"
        assert kwargs["ConfirmationCode"] == "123456"

    async def test_wrong_code_returns_400(self, client, idp):
        idp.confirm_sign_up.side_effect = _client_error("CodeMismatchException", "bad code")
        r = await client.post(
            "/api/v1/auth/confirm", json={"email": "new@example.com", "code": "000000"}
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "Invalid verification code."

    async def test_expired_code_returns_400_asking_for_a_new_one(self, client, idp):
        idp.confirm_sign_up.side_effect = _client_error("ExpiredCodeException", "expired")
        r = await client.post(
            "/api/v1/auth/confirm", json={"email": "new@example.com", "code": "123456"}
        )
        assert r.status_code == 400
        assert "Request a new one" in r.json()["detail"]

    async def test_missing_code_returns_422(self, client, idp):
        r = await client.post("/api/v1/auth/confirm", json={"email": "new@example.com"})
        assert r.status_code == 422


class TestResendCode:
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.resend_confirmation_code.return_value = {}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    async def test_returns_204(self, client, idp):
        r = await client.post("/api/v1/auth/resend-code", json={"email": "new@example.com"})
        assert r.status_code == 204
        assert idp.resend_confirmation_code.call_args.kwargs["Username"] == "new@example.com"

    async def test_throttled_returns_429(self, client, idp):
        idp.resend_confirmation_code.side_effect = _client_error(
            "LimitExceededException", "Attempt limit exceeded"
        )
        r = await client.post("/api/v1/auth/resend-code", json={"email": "new@example.com"})
        assert r.status_code == 429

    async def test_unreachable_cognito_returns_503(self, client, idp):
        idp.resend_confirmation_code.side_effect = EndpointConnectionError(
            endpoint_url="https://cognito-idp"
        )
        r = await client.post("/api/v1/auth/resend-code", json={"email": "new@example.com"})
        assert r.status_code == 503


class TestRefresh:
    _BODY = {"refresh_token": "refresh-tok", "username": _NEW_SUB}

    @pytest.fixture
    def idp(self):
        auth = {k: v for k, v in _AUTH_RESULT.items() if k != "RefreshToken"}
        auth["IdToken"] = jwt.encode({"email": "user@example.com"}, "x" * 32, algorithm="HS256")
        idp = MagicMock()
        idp.initiate_auth.return_value = {"AuthenticationResult": auth}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture(autouse=True)
    def verify(self):
        claims = {"sub": _NEW_SUB, "username": _NEW_SUB}
        with patch("app.api.v1.endpoints.auth.sign_in.verify_access_token", return_value=claims):
            yield

    async def test_returns_new_tokens_and_keeps_the_refresh_token(self, client, idp):
        r = await client.post("/api/v1/auth/refresh", json=self._BODY)
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] == "access-tok"
        assert body["refresh_token"] == "refresh-tok"
        assert body["user"] == {"id": _NEW_SUB, "email": "user@example.com", "username": _NEW_SUB}

    async def test_secret_hash_is_built_from_the_cognito_username(self, client, idp):
        from app.core.cognito import secret_hash

        await client.post("/api/v1/auth/refresh", json=self._BODY)
        kwargs = idp.initiate_auth.call_args.kwargs
        assert kwargs["AuthFlow"] == "REFRESH_TOKEN_AUTH"
        assert kwargs["AuthParameters"]["SECRET_HASH"] == secret_hash(_NEW_SUB)

    async def test_rejected_refresh_token_returns_401(self, client, idp):
        idp.initiate_auth.side_effect = _client_error("NotAuthorizedException", "expired")
        r = await client.post("/api/v1/auth/refresh", json=self._BODY)
        assert r.status_code == 401
        assert "sign in again" in r.json()["detail"]

    async def test_unreachable_cognito_returns_503(self, client, idp):
        idp.initiate_auth.side_effect = EndpointConnectionError(endpoint_url="https://cognito-idp")
        r = await client.post("/api/v1/auth/refresh", json=self._BODY)
        assert r.status_code == 503

    async def test_missing_username_returns_422(self, client):
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "refresh-tok"})
        assert r.status_code == 422


class TestForgotPassword:
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.forgot_password.return_value = {}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    async def test_returns_204(self, client, idp):
        r = await client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
        assert r.status_code == 204
        assert idp.forgot_password.call_args.kwargs["Username"] == "user@example.com"

    async def test_unknown_email_also_returns_204(self, client, idp):
        idp.forgot_password.side_effect = _client_error("UserNotFoundException", "no user")
        r = await client.post("/api/v1/auth/forgot-password", json={"email": "who@example.com"})
        assert r.status_code == 204

    async def test_throttled_returns_429(self, client, idp):
        idp.forgot_password.side_effect = _client_error("LimitExceededException", "limit")
        r = await client.post("/api/v1/auth/forgot-password", json={"email": "user@example.com"})
        assert r.status_code == 429


class TestResetPassword:
    _BODY = {"email": "user@example.com", "code": " 123456 ", "password": "new-securepass"}

    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.confirm_forgot_password.return_value = {}
        with patch("app.core.cognito.get_idp_client", return_value=idp):
            yield idp

    async def test_returns_204_and_sends_code_and_new_password(self, client, idp):
        r = await client.post("/api/v1/auth/reset-password", json=self._BODY)
        assert r.status_code == 204
        kwargs = idp.confirm_forgot_password.call_args.kwargs
        assert kwargs["ConfirmationCode"] == "123456"
        assert kwargs["Password"] == "new-securepass"

    @pytest.mark.parametrize("code", ["CodeMismatchException", "UserNotFoundException"])
    async def test_bad_code_and_unknown_email_look_the_same(self, client, idp, code):
        idp.confirm_forgot_password.side_effect = _client_error(code, "nope")
        r = await client.post("/api/v1/auth/reset-password", json=self._BODY)
        assert r.status_code == 400
        assert r.json()["detail"] == "Invalid verification code."

    async def test_expired_code_returns_400(self, client, idp):
        idp.confirm_forgot_password.side_effect = _client_error("ExpiredCodeException", "old")
        r = await client.post("/api/v1/auth/reset-password", json=self._BODY)
        assert r.status_code == 400
        assert "Request a new one" in r.json()["detail"]

    async def test_weak_password_returns_422(self, client, idp):
        idp.confirm_forgot_password.side_effect = _client_error(
            "InvalidPasswordException", "Password must have symbol characters"
        )
        r = await client.post("/api/v1/auth/reset-password", json=self._BODY)
        assert r.status_code == 422
        assert "symbol" in r.json()["detail"]

    async def test_short_password_rejected_before_cognito(self, client, idp):
        r = await client.post(
            "/api/v1/auth/reset-password", json={**self._BODY, "password": "short"}
        )
        assert r.status_code == 422
        idp.confirm_forgot_password.assert_not_called()


class TestOAuthExchange:
    _BODY = {"code": "auth-code", "redirect_uri": "http://localhost:3000/auth/callback"}
    _TOKENS = {
        "access_token": "access-tok",
        "id_token": "id-tok",
        "refresh_token": "refresh-tok",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    _GOOGLE_SUB = "6f1c2a9e-0000-4000-8000-000000000003"
    _GOOGLE_CLAIMS = {
        "sub": _GOOGLE_SUB,
        "email": "g@example.com",
        "given_name": "Grace",
        "family_name": "Hopper",
    }

    @pytest.fixture
    def token_endpoint(self, monkeypatch):
        """Route the module's httpx client to an in-process handler; record requests."""
        state = {"status": 200, "json": dict(self._TOKENS), "requests": []}

        def handler(request: httpx.Request) -> httpx.Response:
            state["requests"].append(request)
            return httpx.Response(state["status"], json=state["json"])

        transport = httpx.MockTransport(handler)
        fake_httpx = SimpleNamespace(
            AsyncClient=lambda **kw: httpx.AsyncClient(transport=transport, **kw),
            HTTPError=httpx.HTTPError,
        )
        monkeypatch.setattr("app.api.v1.endpoints.auth.oauth.httpx", fake_httpx)
        monkeypatch.setattr(
            "app.api.v1.endpoints.auth.oauth.settings.cognito_domain",
            "https://radestate.auth.us-east-1.amazoncognito.com/",
        )
        return state

    @pytest.fixture(autouse=True)
    def verify(self):
        with (
            patch(
                "app.api.v1.endpoints.auth.oauth.verify_id_token",
                return_value=dict(self._GOOGLE_CLAIMS),
            ) as id_mock,
            patch(
                "app.api.v1.endpoints.auth.sign_in.verify_access_token",
                return_value={"sub": self._GOOGLE_SUB, "username": "google_1234"},
            ),
        ):
            yield id_mock

    @pytest.fixture
    def profiles(self):
        with (
            patch(
                "app.api.v1.endpoints.auth.oauth.get_profile_row",
                new_callable=AsyncMock,
                return_value=None,
            ) as get_row,
            patch(
                "app.api.v1.endpoints.auth.oauth.upsert_profile_patch",
                new_callable=AsyncMock,
            ) as upsert,
        ):
            yield SimpleNamespace(get_row=get_row, upsert=upsert)

    async def test_returns_session_for_the_google_user(self, client, token_endpoint, profiles):
        r = await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] == "access-tok"
        assert body["refresh_token"] == "refresh-tok"
        assert body["user"] == {
            "id": self._GOOGLE_SUB,
            "email": "g@example.com",
            "username": "google_1234",
        }

    async def test_posts_code_to_the_token_endpoint_with_client_auth(
        self, client, token_endpoint, profiles
    ):
        await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        (request,) = token_endpoint["requests"]
        assert str(request.url) == "https://radestate.auth.us-east-1.amazoncognito.com/oauth2/token"
        assert request.headers["authorization"].startswith("Basic ")
        form = dict(httpx.QueryParams(request.content.decode()))
        assert form["grant_type"] == "authorization_code"
        assert form["code"] == "auth-code"
        assert form["redirect_uri"] == "http://localhost:3000/auth/callback"

    async def test_new_profile_takes_names_from_google(self, client, token_endpoint, profiles):
        await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        user_id, patch_body = profiles.upsert.call_args.args[1:]
        assert str(user_id) == self._GOOGLE_SUB
        assert (patch_body.email, patch_body.first_name, patch_body.last_name) == (
            "g@example.com",
            "Grace",
            "Hopper",
        )

    async def test_existing_names_are_kept(self, client, token_endpoint, profiles):
        profiles.get_row.return_value = {"first_name": "Amazing", "last_name": "Grace"}
        await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        patch_body = profiles.upsert.call_args.args[2]
        assert (patch_body.first_name, patch_body.last_name) == ("Amazing", "Grace")

    async def test_profile_failure_does_not_block_sign_in(self, client, token_endpoint, profiles):
        from app.core.db_safe import SupabaseRequestError

        profiles.upsert.side_effect = SupabaseRequestError("down")
        r = await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        assert r.status_code == 200

    async def test_rejected_code_returns_400(self, client, token_endpoint, profiles):
        token_endpoint["status"] = 400
        token_endpoint["json"] = {"error": "invalid_grant"}
        r = await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        assert r.status_code == 400
        assert "Google sign-in" in r.json()["detail"]
        profiles.upsert.assert_not_called()

    async def test_token_endpoint_outage_returns_503(self, client, token_endpoint, profiles):
        token_endpoint["status"] = 502
        r = await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        assert r.status_code == 503

    async def test_invalid_id_token_returns_400(self, client, token_endpoint, profiles, verify):
        verify.side_effect = jwt.InvalidAudienceError("aud")
        r = await client.post("/api/v1/auth/oauth/exchange", json=self._BODY)
        assert r.status_code == 400
        profiles.upsert.assert_not_called()
