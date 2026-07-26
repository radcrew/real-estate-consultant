"""HTTP client for the radestate FastAPI backend."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.client.errors import AuthRequiredError
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

    def require_auth(self) -> None:
        if not (self._access_token and self._access_token.strip()):
            raise AuthRequiredError()

    def _headers(self, *, auth: bool = False) -> dict[str, str]:
        if auth:
            self.require_auth()
        headers = {"Accept": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        auth: bool = False,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> dict[str, Any] | list[Any]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(auth=auth),
                params=params,
                json=json_body,
            )
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return {}
            data = response.json()
            if not isinstance(data, (dict, list)):
                msg = f"Expected JSON object/array from {path}, got {type(data).__name__}"
                raise TypeError(msg)
            return data

    async def get_json(
        self,
        path: str,
        *,
        auth: bool = False,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = await self._request_json("GET", path, auth=auth, params=params)
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def put_json(
        self,
        path: str,
        body: dict[str, Any],
        *,
        auth: bool = True,
    ) -> dict[str, Any]:
        data = await self._request_json("PUT", path, auth=auth, json_body=body)
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def post_json(
        self,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        auth: bool = True,
    ) -> dict[str, Any]:
        data = await self._request_json("POST", path, auth=auth, json_body=body)
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def ping(self) -> dict[str, Any]:
        """GET /api/v1/ping — backend liveness smoke check."""
        logger.info("backend ping → %s/api/v1/ping", self._base_url)
        return await self.get_json("/api/v1/ping")

    async def search_properties(
        self,
        session_profile_id: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """GET /api/v1/search/{session_profile_id}"""
        return await self.get_json(
            f"/api/v1/search/{session_profile_id}",
            auth=True,
            params={"limit": limit, "offset": offset},
        )

    async def update_search_criteria(
        self,
        session_profile_id: str,
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """PUT /api/v1/search/{session_profile_id} — replaces intake criteria."""
        return await self.put_json(f"/api/v1/search/{session_profile_id}", criteria, auth=True)

    async def get_listing(self, property_id: str) -> dict[str, Any]:
        """GET /api/v1/listings/{property_id}"""
        return await self.get_json(f"/api/v1/listings/{property_id}")

    async def get_featured_listings(self) -> dict[str, Any]:
        """GET /api/v1/listings/featured"""
        return await self.get_json("/api/v1/listings/featured")

    async def explain_fit(self, session_profile_id: str, property_id: str) -> dict[str, Any]:
        """POST /api/v1/search/{session_profile_id}/fit/{property_id}"""
        return await self.post_json(
            f"/api/v1/search/{session_profile_id}/fit/{property_id}",
            body=None,
            auth=True,
        )

    async def list_saved_listings(self) -> dict[str, Any]:
        """GET /api/v1/account/saved"""
        return await self.get_json("/api/v1/account/saved", auth=True)

    async def get_agent(self, broker: str) -> dict[str, Any]:
        """GET /api/v1/agents/{broker}"""
        encoded = quote(broker, safe="")
        return await self.get_json(f"/api/v1/agents/{encoded}", auth=True)
