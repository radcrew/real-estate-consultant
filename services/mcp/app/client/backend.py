"""HTTP client for the radestate FastAPI backend."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class BackendClient:
    """Thin httpx wrapper. Domain logic stays in the backend."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        access_token: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (base_url or settings.backend_api_url).rstrip("/")
        self._access_token = (
            access_token if access_token is not None else settings.mcp_user_access_token
        )
        self._timeout = timeout if timeout is not None else settings.http_timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def get_json(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                msg = f"Expected JSON object from {path}, got {type(data).__name__}"
                raise TypeError(msg)
            return data

    async def ping(self) -> dict[str, Any]:
        """GET /api/v1/ping — backend liveness smoke check."""
        logger.info("backend ping → %s/api/v1/ping", self._base_url)
        return await self.get_json("/api/v1/ping")
