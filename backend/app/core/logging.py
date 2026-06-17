"""Structured JSON logging with per-request context injection, scrubbing, and filtering."""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from contextvars import ContextVar
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
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "request_id": request_id_var.get("-"),
        }
        if (uid := user_id_var.get(None)) is not None:
            payload["user_id"] = uid
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, val in record.__dict__.items():
            if key not in _STDLIB_ATTRS and key not in payload:
                payload[key] = val
        return json.dumps(_scrub(payload), default=str)


class _SolarWindsBulkHandler(logging.Handler):
    """Buffers log records and ships them as a bulk HTTP POST to SolarWinds."""

    def __init__(self, url: str, token: str, capacity: int = 200) -> None:
        super().__init__()
        self._url = url
        self._token = token
        self._capacity = capacity
        self._buffer: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._buffer.append(self.format(record))
            if len(self._buffer) >= self._capacity:
                self.flush()
        except Exception:
            self.handleError(record)

    def flush(self) -> None:
        if not self._buffer:
            return
        lines = self._buffer[:]
        self._buffer.clear()
        try:
            body = "\n".join(lines).encode()
            req = urllib.request.Request(
                self._url,
                data=body,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Authorization": f"Bearer {self._token}",
                },
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass


class _DropNoisyRequestsFilter(logging.Filter):
    """Drop fast, successful requests to noisy paths (e.g. health checks)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "app.request" and record.levelno < logging.WARNING:
            return getattr(record, "path", None) not in _NOISY_PATHS
        return True


_swo_handler: _SolarWindsBulkHandler | None = None


def flush_swo() -> None:
    if _swo_handler is not None:
        _swo_handler.flush()


def configure_logging(
    level: str = "INFO",
    swo_logs_url: str = "",
    swo_token: str = "",
) -> None:
    global _swo_handler

    formatter = _JsonFormatter()
    noise_filter = _DropNoisyRequestsFilter()

    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(formatter)
    stdout_handler.addFilter(noise_filter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(stdout_handler)

    if swo_logs_url and swo_token:
        _swo_handler = _SolarWindsBulkHandler(url=swo_logs_url, token=swo_token)
        _swo_handler.setFormatter(formatter)
        _swo_handler.addFilter(noise_filter)
        root.addHandler(_swo_handler)

    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
