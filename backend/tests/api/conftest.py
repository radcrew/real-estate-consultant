"""Shared fixtures for API endpoint tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.deps import get_current_user
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
def mock_user():
    user = MagicMock()
    user.id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    user.email = "user@example.com"
    return user


@pytest.fixture
async def client(mock_db, mock_supabase, mock_user):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
