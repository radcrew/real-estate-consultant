"""Low-level helper to raise FastAPI ``HTTPException`` with optional exception chaining."""

from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException


def raise_http_exception(
    status_code: int,
    detail: str,
    *,
    cause: BaseException | None = None,
) -> NoReturn:
    raise HTTPException(status_code=status_code, detail=detail) from cause
