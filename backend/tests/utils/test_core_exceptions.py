import pytest
from fastapi import HTTPException

from app.core.exceptions import (
    raise_auth_invalid_access_token,
    raise_auth_missing_bearer,
    raise_auth_user_not_returned,
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
        from supabase import AuthApiError
        cause = AuthApiError("expired", status=401, code="token_expired")
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_invalid_access_token(cause=cause)
        assert exc_info.value.__cause__ is cause

    def test_user_not_returned_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_auth_user_not_returned()
        assert exc_info.value.status_code == 401
