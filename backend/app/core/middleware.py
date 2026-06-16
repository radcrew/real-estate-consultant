"""ASGI middleware: request ID stamping, timing, and per-request log events."""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from app.core.logging import request_id_var, user_id_var

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.request")

SLOW_REQUEST_THRESHOLD_MS = 3000.0


class RequestLoggingMiddleware:
    """Stamp a request ID, time the request, and emit one structured log event."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        request_id_var.set(request_id)
        user_id_var.set(None)

        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append(
                    (b"x-request-id", request_id.encode())
                )
            await send(message)

        start = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            is_slow = duration_ms > SLOW_REQUEST_THRESHOLD_MS
            logger.log(
                logging.WARNING if is_slow else logging.INFO,
                "request_slow" if is_slow else "request_completed",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
