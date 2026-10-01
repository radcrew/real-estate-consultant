"""Unit tests for Cognito SECRET_HASH and access-token verification."""

from __future__ import annotations

import time
from types import SimpleNamespace

import jwt
import pytest
from botocore import UNSIGNED
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import cognito
from app.core.config import settings

REGION = "us-east-1"
POOL_ID = "us-east-1_TestPool"
CLIENT_ID = "test-client-id"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class _StaticJwks:
    def __init__(self, key):
        self._key = key

    def get_signing_key_from_jwt(self, _token):
        return SimpleNamespace(key=self._key)


@pytest.fixture(autouse=True)
def cognito_settings(monkeypatch):
    monkeypatch.setattr(settings, "cognito_region", REGION)
    monkeypatch.setattr(settings, "cognito_user_pool_id", POOL_ID)
    monkeypatch.setattr(settings, "cognito_client_id", CLIENT_ID)
    monkeypatch.setattr(settings, "cognito_client_secret", "client-secret")
    monkeypatch.setattr(cognito, "_jwks_client", lambda _url: _StaticJwks(_KEY.public_key()))


def _token(*, key=_KEY, **overrides) -> str:
    claims = {
        "iss": ISSUER,
        "sub": "6f1c2a9e-0000-4000-8000-000000000001",
        "token_use": "access",
        "client_id": CLIENT_ID,
        "username": "user@example.com",
        "exp": int(time.time()) + 300,
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256")


class TestSecretHash:
    def test_matches_a_fixed_vector(self, monkeypatch):
        """Username comes before client id in the HMAC message; swapping them breaks every call."""
        monkeypatch.setattr(settings, "cognito_client_id", "client-id")
        expected = "NpqglvUHBpz0nyO+qeiUjlRR297+e+uA7UhuwY3pkSE="
        assert cognito.secret_hash("user@example.com") == expected


class TestIdpClient:
    def test_is_unsigned_and_uses_the_pool_region(self):
        """Unsigned means no AWS credentials are looked up or required."""
        client = cognito.get_idp_client()
        assert client.meta.region_name == REGION
        assert client.meta.config.signature_version is UNSIGNED


class TestVerifyAccessToken:
    def test_valid_token_returns_claims(self):
        claims = cognito.verify_access_token(_token())
        assert claims["sub"] == "6f1c2a9e-0000-4000-8000-000000000001"
        assert claims["username"] == "user@example.com"

    def test_expired_token_is_rejected(self):
        with pytest.raises(jwt.ExpiredSignatureError):
            cognito.verify_access_token(_token(exp=int(time.time()) - 10))

    def test_other_issuer_is_rejected(self):
        with pytest.raises(jwt.InvalidIssuerError):
            cognito.verify_access_token(_token(iss="https://cognito-idp.us-east-1.amazonaws.com/other"))

    def test_other_app_client_is_rejected(self):
        with pytest.raises(jwt.InvalidTokenError, match="different app client"):
            cognito.verify_access_token(_token(client_id="someone-else"))

    def test_id_token_is_rejected(self):
        with pytest.raises(jwt.InvalidTokenError, match="Not an access token"):
            cognito.verify_access_token(_token(token_use="id", client_id=None, aud=CLIENT_ID))

    def test_token_signed_by_another_key_is_rejected(self):
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with pytest.raises(jwt.InvalidSignatureError):
            cognito.verify_access_token(_token(key=other))

    def test_token_without_sub_is_rejected(self):
        with pytest.raises(jwt.MissingRequiredClaimError):
            cognito.verify_access_token(_token(sub=None))


def _id_token(**overrides) -> str:
    return _token(**{"token_use": "id", "client_id": None, "aud": CLIENT_ID, **overrides})


class TestVerifyIdToken:
    def test_valid_token_returns_claims(self):
        claims = cognito.verify_id_token(_id_token(email="g@example.com"))
        assert claims["email"] == "g@example.com"

    def test_access_token_is_rejected(self):
        with pytest.raises(jwt.InvalidTokenError):
            cognito.verify_id_token(_token())

    def test_other_audience_is_rejected(self):
        with pytest.raises(jwt.InvalidAudienceError):
            cognito.verify_id_token(_id_token(aud="someone-else"))

    def test_other_issuer_is_rejected(self):
        with pytest.raises(jwt.InvalidIssuerError):
            cognito.verify_id_token(
                _id_token(iss="https://cognito-idp.us-east-1.amazonaws.com/other")
            )
