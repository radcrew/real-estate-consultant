import pytest
from fastapi import HTTPException, status

from app.utils.exceptions import (
    raise_bad_gateway,
    raise_bad_request,
    raise_client_error,
    raise_conflict,
    raise_forbidden,
    raise_gateway_timeout,
    raise_http_exception,
    raise_not_found,
    raise_service_unavailable,
    raise_unauthorized,
    raise_unprocessable_entity,
)


class TestRaiseHttpException:
    def test_raises_http_exception_with_status_and_detail(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_http_exception(404, "not found")
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "not found"

    def test_chained_cause_stored(self):
        cause = ValueError("root cause")
        with pytest.raises(HTTPException) as exc_info:
            raise_http_exception(500, "server error", cause=cause)
        assert exc_info.value.__cause__ is cause

    def test_headers_forwarded(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_http_exception(401, "auth", headers={"WWW-Authenticate": "Bearer"})
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestConvenienceRaisers:
    def test_raise_bad_request(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_bad_request("bad input")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_raise_unauthorized(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_unauthorized("no auth", headers={"WWW-Authenticate": "Bearer"})
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_raise_forbidden(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_forbidden("denied")
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_raise_not_found(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_not_found("missing")
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_raise_conflict(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_conflict("already exists")
        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_raise_unprocessable_entity(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_unprocessable_entity("invalid")
        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_raise_bad_gateway(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_bad_gateway("upstream failed")
        assert exc_info.value.status_code == status.HTTP_502_BAD_GATEWAY

    def test_raise_service_unavailable(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_service_unavailable("down")
        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_raise_gateway_timeout(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_gateway_timeout("timeout")
        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    def test_raise_client_error_dynamic_status(self):
        with pytest.raises(HTTPException) as exc_info:
            raise_client_error(429, "rate limited")
        assert exc_info.value.status_code == 429
        assert exc_info.value.detail == "rate limited"
