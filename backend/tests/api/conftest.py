"""Shared fixtures for API endpoint tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.supabase_sdk import get_supabase_sdk_client
from app.main import create_app


@pytest.fixture
def mock_db():
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
async def client(mock_db, mock_supabase):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
