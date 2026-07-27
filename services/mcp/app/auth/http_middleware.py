"""ASGI middleware — capture API key / Bearer from HTTP requests into contextvars."""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from app.auth.context import clear_request_credential, set_request_credential
from app.auth.providers import credential_from_headers

HeaderDict = dict[str, str]


def _headers_map(scope: Scope) -> HeaderDict:
    out: HeaderDict = {}
    for raw_name, raw_value in scope.get("headers") or []:
        name = raw_name.decode("latin-1").lower()
        value = raw_value.decode("latin-1")
        out[name] = value
    return out


class CaptureApiKeyMiddleware:
    """Set request credential for the duration of an HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = _headers_map(scope)
        credential = credential_from_headers(
            headers.get("authorization"),
            headers.get("x-api-key"),
        )
        token = set_request_credential(credential)
        try:
            await self.app(scope, receive, send)
        finally:
            clear_request_credential(token)
