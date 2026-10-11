"""Cognito user pool access: the public auth API client and JWT verification.

Almost every call uses public Cognito APIs authorised by ``SECRET_HASH`` or a user's own
access token, through an unsigned client that needs no IAM credentials. The one exception
is linking a Google sign-in to an existing account, which uses ``call_admin_idp`` and the
standard boto3 credential chain (needs ListUsers, AdminDeleteUser, AdminLinkProviderForUser).
boto3 and ``PyJWKClient`` are synchronous; async callers run them via ``asyncio.to_thread``.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
from functools import cache
from typing import Any

import boto3
import jwt
from botocore import UNSIGNED
from botocore.config import Config

from app.core.config import settings

_JWKS_TIMEOUT_S = 5

# Cognito names a user created by Google sign-in google_<Google id>.
GOOGLE_USERNAME_PREFIX = "google_"


def is_google_username(username: str | None) -> bool:
    """True for a standalone Google user, whose password and email belong to Google."""
    return bool(username) and username.startswith(GOOGLE_USERNAME_PREFIX)


def issuer() -> str:
    return f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/{settings.cognito_user_pool_id}"


@cache
def _idp_client(region: str) -> Any:
    return boto3.client(
        "cognito-idp", region_name=region, config=Config(signature_version=UNSIGNED)
    )


def get_idp_client() -> Any:
    """Unsigned ``cognito-idp`` client for the configured region."""
    return _idp_client(settings.cognito_region)


async def call_idp(operation: str, **params: Any) -> dict[str, Any]:
    """Run one ``cognito-idp`` operation off the event loop. botocore errors propagate."""
    return await asyncio.to_thread(getattr(get_idp_client(), operation), **params)


@cache
def _admin_idp_client(region: str) -> Any:
    return boto3.client("cognito-idp", region_name=region)


async def call_admin_idp(operation: str, **params: Any) -> dict[str, Any]:
    """Run one IAM-signed ``cognito-idp`` admin operation off the event loop."""
    client = _admin_idp_client(settings.cognito_region)
    return await asyncio.to_thread(getattr(client, operation), **params)


@cache
def _jwks_client(jwks_url: str) -> jwt.PyJWKClient:
    # Keys are cached in-process, so the pool's JWKS is fetched once per cold start.
    return jwt.PyJWKClient(jwks_url, timeout=_JWKS_TIMEOUT_S)


def secret_hash(username: str) -> str:
    """``SECRET_HASH`` required by every public API call on a client with a secret."""
    digest = hmac.new(
        settings.cognito_client_secret.encode(),
        (username + settings.cognito_client_id).encode(),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


def _decode(token: str, **kwargs: Any) -> dict[str, Any]:
    iss = issuer()
    signing_key = _jwks_client(f"{iss}/.well-known/jwks.json").get_signing_key_from_jwt(token)
    return jwt.decode(token, signing_key.key, algorithms=["RS256"], issuer=iss, **kwargs)


def verify_id_token(token: str) -> dict[str, Any]:
    """Return the claims of a valid ID token issued to our app client (``aud``)."""
    claims = _decode(
        token,
        audience=settings.cognito_client_id,
        options={"require": ["exp", "iss", "sub", "aud"]},
    )
    if claims.get("token_use") != "id":
        raise jwt.InvalidTokenError("Not an ID token.")
    return claims


def verify_access_token(token: str) -> dict[str, Any]:
    """Return the claims of a valid access token issued to our app client.

    Raises ``jwt.PyJWTError`` for anything else, including ID tokens. Access tokens carry
    ``client_id`` instead of ``aud``, so the audience is checked by hand.
    """
    claims = _decode(token, options={"require": ["exp", "iss", "sub"], "verify_aud": False})
    if claims.get("token_use") != "access":
        raise jwt.InvalidTokenError("Not an access token.")
    if claims.get("client_id") != settings.cognito_client_id:
        raise jwt.InvalidTokenError("Token was issued to a different app client.")
    return claims
