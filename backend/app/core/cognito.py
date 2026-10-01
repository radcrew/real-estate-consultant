"""Cognito user pool access: the public auth API client and JWT verification.

Every call here uses public Cognito APIs authorised by ``SECRET_HASH`` or a user's own
access token, so the boto3 client is unsigned and the backend needs no IAM credentials.
boto3 and ``PyJWKClient`` are synchronous; async callers run them via ``asyncio.to_thread``.
"""

from __future__ import annotations

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


def verify_access_token(token: str) -> dict[str, Any]:
    """Return the claims of a valid access token issued to our app client.

    Raises ``jwt.PyJWTError`` for anything else, including ID tokens. Access tokens carry
    ``client_id`` instead of ``aud``, so the audience is checked by hand.
    """
    iss = issuer()
    signing_key = _jwks_client(f"{iss}/.well-known/jwks.json").get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=iss,
        options={"require": ["exp", "iss", "sub"], "verify_aud": False},
    )
    if claims.get("token_use") != "access":
        raise jwt.InvalidTokenError("Not an access token.")
    if claims.get("client_id") != settings.cognito_client_id:
        raise jwt.InvalidTokenError("Token was issued to a different app client.")
    return claims
