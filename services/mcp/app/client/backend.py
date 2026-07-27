"""HTTP client for the radestate FastAPI backend."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.auth import AuthRequiredError, get_backend_credential
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
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = await self._request_json(
            "POST",
            path,
            auth=auth,
            params=params,
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
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = await self._request_json(
            "PATCH",
            path,
            auth=auth,
            params=params,
            json_body=body,
        )
        if not isinstance(data, dict):
            msg = f"Expected JSON object from {path}, got {type(data).__name__}"
            raise TypeError(msg)
        return data

    async def ping(self) -> dict[str, Any]:
        """GET /api/v1/ping — backend liveness smoke check."""
        logger.info("backend ping → %s/api/v1/ping", self._base_url)
        return await self.get_json("/api/v1/ping")

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

    async def start_intake_session(self, mode: str = "guided") -> dict[str, Any]:
        """POST /api/v1/intake-sessions/?mode=guided|llm"""
        return await self.post_json(
            "/api/v1/intake-sessions/",
            body=None,
            auth=True,
            params={"mode": mode},
        )

    async def get_intake_session(self, session_id: str) -> dict[str, Any]:
        """GET /api/v1/intake-sessions/{session_id}"""
        return await self.get_json(f"/api/v1/intake-sessions/{session_id}", auth=True)

    async def answer_intake_guided(
        self,
        session_id: str,
        *,
        key: str,
        answers: Any,
    ) -> dict[str, Any]:
        """PATCH /api/v1/intake-sessions/{session_id}/answers/guided"""
        return await self.patch_json(
            f"/api/v1/intake-sessions/{session_id}/answers/guided",
            {"key": key, "answers": answers},
            auth=True,
        )

    async def answer_intake_llm(self, session_id: str, *, text: str) -> dict[str, Any]:
        """POST /api/v1/intake-sessions/{session_id}/answers/llm"""
        return await self.post_json(
            f"/api/v1/intake-sessions/{session_id}/answers/llm",
            {"input": text, "mode": "llm"},
            auth=True,
        )

    async def complete_intake_session(self, session_id: str) -> dict[str, Any]:
        """POST /api/v1/intake-sessions/{session_id}/complete"""
        return await self.post_json(
            f"/api/v1/intake-sessions/{session_id}/complete",
            body=None,
            auth=True,
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

    async def enqueue_ingest(self, source: str = "loopnet-seed") -> dict[str, Any]:
        """POST /api/v1/admin/ingest — admin JWT required (backend enforces)."""
        return await self.post_json(
            "/api/v1/admin/ingest",
            {"source": source},
            auth=True,
        )

    async def list_listing_submissions(self) -> list[Any]:
        """GET /api/v1/listing-submissions — admin JWT required."""
        data = await self._request_json(
            "GET",
            "/api/v1/listing-submissions",
            auth=True,
        )
        if not isinstance(data, list):
            msg = f"Expected JSON array from listing-submissions, got {type(data).__name__}"
            raise TypeError(msg)
        return data
