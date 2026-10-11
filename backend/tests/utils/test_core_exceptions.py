import pytest
from fastapi import HTTPException

from app.core.exceptions import (
    raise_auth_invalid_access_token,
    raise_auth_missing_bearer,
    raise_auth_provider_unavailable,
)


class TestCoreExceptions:
    def test_missing_bearer_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_missing_bearer()
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_invalid_access_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_invalid_access_token()
        assert exc_info.value.status_code == 401
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_invalid_access_token_with_cause(self):
        import jwt
        cause = jwt.ExpiredSignatureError("Signature has expired")
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_invalid_access_token(cause=cause)
        assert exc_info.value.__cause__ is cause

    def test_provider_unavailable_raises_503(self):
        cause = ConnectionError("jwks down")
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_provider_unavailable(cause=cause)
        assert exc_info.value.status_code == 503
        assert exc_info.value.__cause__ is cause
