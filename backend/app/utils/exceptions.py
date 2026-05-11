"""Low-level helper to raise FastAPI ``HTTPException`` with optional exception chaining."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status


def raise_http_exception(
    status_code: int,
    detail: str,
    *,
    cause: BaseException | None = None,
    headers: dict[str, str] | None = None,
) -> NoReturn:
    raise HTTPException(status_code=status_code, detail=detail, headers=headers) from cause


def raise_bad_request(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_400_BAD_REQUEST, detail, cause=cause)


def raise_unauthorized(
    detail: str,
    *,
    cause: BaseException | None = None,
    headers: dict[str, str] | None = None,
) -> NoReturn:
    raise_http_exception(status.HTTP_401_UNAUTHORIZED, detail, cause=cause, headers=headers)


def raise_forbidden(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_403_FORBIDDEN, detail, cause=cause)


def raise_not_found(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_404_NOT_FOUND, detail, cause=cause)


def raise_conflict(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_409_CONFLICT, detail, cause=cause)


def raise_unprocessable_entity(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, cause=cause)


def raise_bad_gateway(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_502_BAD_GATEWAY, detail, cause=cause)


def raise_service_unavailable(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_503_SERVICE_UNAVAILABLE, detail, cause=cause)


def raise_gateway_timeout(detail: str, *, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(status.HTTP_504_GATEWAY_TIMEOUT, detail, cause=cause)


def raise_client_error(
    status_code: int,
    detail: str,
    *,
    cause: BaseException | None = None,
) -> NoReturn:
    """When ``status_code`` is dynamic (e.g. Supabase ``AuthApiError.status``)."""
    raise_http_exception(status_code, detail, cause=cause)
