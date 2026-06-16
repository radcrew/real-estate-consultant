"""Structured JSON logging with per-request context injection, scrubbing, and filtering."""

from __future__ import annotations

import json
import logging
import re
import socket
from contextvars import ContextVar
from logging.handlers import SysLogHandler
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

_STDLIB_ATTRS: frozenset[str] = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName", "asctime",
})

# Paths whose successful, fast requests are too noisy to log (e.g. health probes).
_NOISY_PATHS: frozenset[str] = frozenset({"/health"})

# Keys whose values are always redacted, regardless of content.
_REDACT_KEYS: frozenset[str] = frozenset({
    "password", "token", "access_token", "refresh_token", "authorization",
    "api_key", "hf_token", "secret",
})

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_REDACTED = "***"


def _scrub(value: Any, key: str | None = None) -> Any:
    """Redact sensitive keys and mask email addresses in log payloads."""
    if key is not None and key.lower() in _REDACT_KEYS:
        return _REDACTED
    if isinstance(value, str):
        return _EMAIL_RE.sub(_REDACTED, value)
    if isinstance(value, dict):
        return {k: _scrub(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


class _JsonFormatter(logging.Formatter):
    def __init__(self, swo_token: str = "") -> None:
        super().__init__()
        self._swo_token = swo_token

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "request_id": request_id_var.get("-"),
        }
        if self._swo_token:
            payload["swo_token"] = self._swo_token
        if (uid := user_id_var.get(None)) is not None:
            payload["user_id"] = uid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, val in record.__dict__.items():
            if key not in _STDLIB_ATTRS and key not in payload:
                payload[key] = val
        return json.dumps(_scrub(payload), default=str)


class _DropNoisyRequestsFilter(logging.Filter):
    """Drop fast, successful requests to noisy paths (e.g. health checks)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "app.request" and record.levelno < logging.WARNING:
            return getattr(record, "path", None) not in _NOISY_PATHS
        return True


def configure_logging(
    level: str = "INFO",
    swo_hostname: str = "",
    swo_port: int = 514,
    swo_token: str = "",
) -> None:
    formatter = _JsonFormatter(swo_token=swo_token)
    noise_filter = _DropNoisyRequestsFilter()

    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(noise_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(stdout_handler)

    if swo_hostname and swo_token:
        swo_handler = SysLogHandler(
            address=(swo_hostname, swo_port),
            socktype=socket.SOCK_DGRAM,
        )
        swo_handler.setFormatter(formatter)
        swo_handler.addFilter(noise_filter)
        root.addHandler(swo_handler)

    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
