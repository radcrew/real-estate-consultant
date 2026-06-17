"""Tests for wake_processor service function."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ingestion import wake_processor


class TestWakeProcessor:
    async def test_no_op_when_url_not_configured(self):
        with patch("app.services.ingestion.settings") as mock_settings:
            mock_settings.ingestion_service_url = ""
            # Should return without calling anything
            await wake_processor()

    async def test_calls_process_jobs_when_url_set(self):
        result = MagicMock()
        result.processed = True
        result.job_id = "job-1"
        result.status = "complete"

        mock_client = MagicMock()
        mock_client.process_jobs = AsyncMock(return_value=result)

        with (
            patch("app.services.ingestion.settings") as mock_settings,
            patch("app.services.ingestion.IngestionClient", return_value=mock_client),
        ):
            mock_settings.ingestion_service_url = "https://ingest.example.com"
            mock_settings.ingestion_service_token = "secret"
            await wake_processor()

        mock_client.process_jobs.assert_called_once()

    async def test_http_error_is_swallowed(self):
        mock_client = MagicMock()
        mock_client.process_jobs = AsyncMock(side_effect=httpx.ConnectError("timeout"))

        with (
            patch("app.services.ingestion.settings") as mock_settings,
            patch("app.services.ingestion.IngestionClient", return_value=mock_client),
        ):
            mock_settings.ingestion_service_url = "https://ingest.example.com"
            mock_settings.ingestion_service_token = "secret"
            # Should not raise — failures are logged and swallowed
            await wake_processor()
