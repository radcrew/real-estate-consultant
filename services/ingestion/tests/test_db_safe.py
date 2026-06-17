"""Tests for app.core.db_safe — Supabase call wrapper."""
import pytest
from unittest.mock import AsyncMock
import httpx
from postgrest.exceptions import APIError

from app.core.db_safe import SupabaseRequestError, execute_db_safe


class TestExecuteDbSafe:
    @pytest.mark.asyncio
    async def test_returns_result_on_success(self):
        awaitable = AsyncMock(return_value="ok")()
        result = await execute_db_safe(awaitable)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_raises_supabase_error_on_api_error(self):
        async def bad():
            raise APIError({"message": "not found", "code": "404", "details": "", "hint": ""})

        with pytest.raises(SupabaseRequestError, match="PostgREST"):
            await execute_db_safe(bad())

    @pytest.mark.asyncio
    async def test_raises_supabase_error_on_http_error(self):
        async def bad():
            raise httpx.ConnectError("refused")

        with pytest.raises(SupabaseRequestError, match="Supabase"):
            await execute_db_safe(bad())

    @pytest.mark.asyncio
    async def test_does_not_catch_other_exceptions(self):
        async def bad():
            raise ValueError("unexpected")

        with pytest.raises(ValueError):
            await execute_db_safe(bad())
