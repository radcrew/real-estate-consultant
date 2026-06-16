"""Typed HTTP client for the ingestion microservice.

Request/response models in ``models.py`` are generated from the ingestion
service's OpenAPI schema — see ``scripts/generate_ingestion_models.py``. A
contract change there regenerates (or fails to match) this client, so
mismatches surface at build time instead of at runtime.
"""

from __future__ import annotations

import httpx

from app.clients.ingestion.models import ProcessResponse

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


class IngestionClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def process_jobs(self) -> ProcessResponse:
        """Call ``POST /api/v1/jobs/process`` to claim and run the next pending job."""
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base_url}/api/v1/jobs/process",
                headers={"Authorization": f"Bearer {self._token}"},
            )
            resp.raise_for_status()
            return ProcessResponse.model_validate(resp.json())
