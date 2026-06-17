"""Tests for IngestionClient HTTP wrapper."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.clients.ingestion.client import IngestionClient
from app.clients.ingestion.models import ProcessResponse


class TestIngestionClient:
    async def test_process_jobs_returns_response(self):
        payload = {"processed": True, "job_id": "j1", "source": "loopnet", "status": "done", "message": None}
        mock_resp = MagicMock()
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("app.clients.ingestion.client.httpx.AsyncClient", return_value=mock_http):
            client = IngestionClient("https://ingest.example.com", "secret-token")
            result = await client.process_jobs()

        assert isinstance(result, ProcessResponse)
        assert result.processed is True
        assert result.job_id == "j1"

    async def test_http_error_propagates(self):
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        with patch("app.clients.ingestion.client.httpx.AsyncClient", return_value=mock_http):
            client = IngestionClient("https://ingest.example.com", "token")
            with pytest.raises(httpx.HTTPError):
                await client.process_jobs()

    async def test_base_url_trailing_slash_stripped(self):
        payload = {"processed": False, "job_id": None, "source": None, "status": None, "message": None}
        mock_resp = MagicMock()
        mock_resp.json.return_value = payload
        mock_resp.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.post = AsyncMock(return_value=mock_resp)

        with patch("app.clients.ingestion.client.httpx.AsyncClient", return_value=mock_http) as MockClient:
            client = IngestionClient("https://ingest.example.com/", "token")
            await client.process_jobs()

        call_args = mock_http.post.call_args
        assert "https://ingest.example.com/api/v1/jobs/process" == call_args[0][0]
