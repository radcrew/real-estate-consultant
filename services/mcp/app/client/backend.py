"""HTTP client for the radestate FastAPI backend."""

from __future__ import annotations

from typing import Any

import httpx

from app.auth import AuthRequiredError, get_backend_credential
from app.config import settings


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
        # Explicit token wins (tests); otherwise resolve API key / JWT / request header.
        self._access_token = access_token
        self._timeout = timeout if timeout is not None else settings.http_timeout_seconds

    def _credential(self) -> str:
        if self._access_token is not None:
            token = self._access_token.strip()
            if not token:
                raise AuthRequiredError()
            return token
        return get_backend_credential()

    def require_auth(self) -> None:
        self._credential()

    def _headers(self, *, auth: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {self._credential()}"
        elif self._access_token is not None and self._access_token.strip():
            headers["Authorization"] = f"Bearer {self._access_token.strip()}"
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
        data = await self._request_json(
            "POST",
            path,
            auth=auth,
            json_body=body,
        )
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def patch_json(
        self,
        path: str,
        body: dict[str, Any],
        *,
        auth: bool = True,
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PATCH",
            path,
            auth=auth,
            json_body=body,
        )
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def quick_search(
        self,
        *,
        location: str | None = None,
        property_types: list[str] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
    ) -> dict[str, Any]:
        """POST /api/v1/search/quick — create a search profile from hero filters."""
        body: dict[str, Any] = {}
        if location:
            body["location"] = location
        if property_types:
            body["property_types"] = property_types
        if price_min is not None:
            body["price_min"] = price_min
        if price_max is not None:
            body["price_max"] = price_max
        return await self.post_json("/api/v1/search/quick", body, auth=True)

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
        """PUT /api/v1/search/{session_profile_id} — replaces search criteria."""
        return await self.put_json(f"/api/v1/search/{session_profile_id}", criteria, auth=True)

    async def get_listing(self, property_id: str) -> dict[str, Any]:
        """GET /api/v1/listings/{property_id}"""
        return await self.get_json(f"/api/v1/listings/{property_id}")

    async def get_featured_listings(self) -> dict[str, Any]:
        """GET /api/v1/listings/featured"""
        return await self.get_json("/api/v1/listings/featured")

    async def get_similar_listings(
        self,
        property_id: str,
        *,
        limit: int = 6,
    ) -> dict[str, Any]:
        """GET /api/v1/listings/{property_id}/similar"""
        return await self.get_json(
            f"/api/v1/listings/{property_id}/similar",
            params={"limit": limit},
        )

    async def generate_outreach_draft(self, property_id: str) -> dict[str, Any]:
        """POST /api/v1/outreach/drafts — creates a draft only (never sends)."""
        return await self.post_json(
            "/api/v1/outreach/drafts",
            {"property_id": property_id},
            auth=True,
        )

    async def get_outreach_draft(self, draft_id: str) -> dict[str, Any]:
        """GET /api/v1/outreach/drafts/{draft_id}"""
        return await self.get_json(f"/api/v1/outreach/drafts/{draft_id}", auth=True)

    async def get_latest_outreach_draft(self, property_id: str) -> dict[str, Any]:
        """GET /api/v1/outreach/drafts/latest?property_id=…"""
        return await self.get_json(
            "/api/v1/outreach/drafts/latest",
            auth=True,
            params={"property_id": property_id},
        )

    async def update_outreach_draft(self, draft_id: str, draft_email: str) -> dict[str, Any]:
        """PATCH /api/v1/outreach/drafts/{draft_id}"""
        return await self.patch_json(
            f"/api/v1/outreach/drafts/{draft_id}",
            {"draft_email": draft_email},
            auth=True,
        )
