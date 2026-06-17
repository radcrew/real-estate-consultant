import pytest
import httpx
from postgrest.exceptions import APIError

from app.core.db_safe import SupabaseRequestError, execute_db_safe


class TestExecuteDbSafe:
    async def test_success_returns_result(self):
        async def _ok():
            return {"id": 1}

        result = await execute_db_safe(_ok())
        assert result == {"id": 1}

    async def test_api_error_raises_supabase_request_error(self):
        async def _fail():
            raise APIError({"message": "relation does not exist", "code": "42P01", "details": None, "hint": None})

        with pytest.raises(SupabaseRequestError):
            await execute_db_safe(_fail())

    async def test_api_error_schema_cache_hint(self):
        async def _fail():
            raise APIError({"message": "pgrst204 schema cache stale", "code": "PGRST204", "details": None, "hint": None})

        with pytest.raises(SupabaseRequestError):
            await execute_db_safe(_fail())

    async def test_http_error_raises_supabase_request_error(self):
        async def _fail():
            raise httpx.ConnectError("cannot connect")

        with pytest.raises(SupabaseRequestError):
            await execute_db_safe(_fail())

    async def test_chained_cause_preserved(self):
        original = APIError({"message": "bad", "code": "500", "details": None, "hint": None})

        async def _fail():
            raise original

        with pytest.raises(SupabaseRequestError) as info:
            await execute_db_safe(_fail())
        assert info.value.__cause__ is original
