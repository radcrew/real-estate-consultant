"""Tests for POST /api/v1/listing-submissions/images (file upload)."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_upload(content: bytes, content_type: str, filename: str = "photo.jpg"):
    return (filename, BytesIO(content), content_type)


class TestUploadSubmissionImages:
    async def test_success_returns_urls(self, mock_supabase):
        storage_mock = AsyncMock()
        storage_mock.upload = AsyncMock()
        storage_mock.get_public_url = AsyncMock(return_value="https://example.com/img.jpg")
        mock_supabase.storage.from_.return_value = storage_mock

        from app.main import create_app
        from app.core.database import get_session
        from app.core.deps import get_current_user
        from app.core.supabase_sdk import get_supabase_sdk_client
        from httpx import ASGITransport, AsyncClient
        from unittest.mock import MagicMock

        app = create_app()
        app.dependency_overrides[get_session] = lambda: AsyncMock()
        app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
        app.dependency_overrides[get_current_user] = lambda: MagicMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.post(
                "/api/v1/listing-submissions/images",
                files=[("files", ("photo.jpg", BytesIO(b"fake-image-data"), "image/jpeg"))],
            )
        assert r.status_code == 200
        assert r.json()["urls"] == ["https://example.com/img.jpg"]

    async def test_no_files_returns_400(self, client):
        r = await client.post("/api/v1/listing-submissions/images", files=[])
        assert r.status_code in (400, 422)

    async def test_too_many_files_returns_400(self, client, mock_supabase):
        files = [("files", (f"img{i}.jpg", BytesIO(b"data"), "image/jpeg")) for i in range(11)]
        r = await client.post("/api/v1/listing-submissions/images", files=files)
        assert r.status_code == 400

    async def test_invalid_content_type_returns_400(self, client, mock_supabase):
        storage_mock = AsyncMock()
        mock_supabase.storage.from_.return_value = storage_mock
        r = await client.post(
            "/api/v1/listing-submissions/images",
            files=[("files", ("doc.pdf", BytesIO(b"pdf-data"), "application/pdf"))],
        )
        assert r.status_code == 400

    async def test_oversized_file_returns_400(self, client, mock_supabase):
        storage_mock = AsyncMock()
        mock_supabase.storage.from_.return_value = storage_mock
        big_data = b"x" * (5 * 1024 * 1024 + 1)
        r = await client.post(
            "/api/v1/listing-submissions/images",
            files=[("files", ("big.jpg", BytesIO(big_data), "image/jpeg"))],
        )
        assert r.status_code == 400
