from uuid import UUID

from app.repositories.jobs import get_active_job_by_idempotency_key, get_job_row, insert_job_row
from tests.repositories.conftest import make_supabase_client

_JOB_ROW = {"id": "job-1", "source": "loopnet-seed", "status": "pending"}


class TestGetActiveJobByIdempotencyKey:
    async def test_returns_row_when_active_job_exists(self):
        client = make_supabase_client([{"id": "job-1", "status": "pending"}])
        result = await get_active_job_by_idempotency_key(client, "loopnet-seed:2026-01-01")
        assert result == {"id": "job-1", "status": "pending"}

    async def test_returns_none_when_no_active_job(self):
        client = make_supabase_client([])
        result = await get_active_job_by_idempotency_key(client, "loopnet-seed:2026-01-01")
        assert result is None

    async def test_filters_by_idempotency_key_and_active_statuses(self):
        client = make_supabase_client([])
        await get_active_job_by_idempotency_key(client, "loopnet-seed:2026-01-01")
        table = client.table.return_value
        table.eq.assert_called_once_with("idempotency_key", "loopnet-seed:2026-01-01")
        table.in_.assert_called_once_with("status", ("pending", "running"))


class TestInsertJobRow:
    async def test_returns_inserted_row(self):
        client = make_supabase_client([_JOB_ROW])
        result = await insert_job_row(client, source="loopnet-seed", idempotency_key="k")
        assert result == _JOB_ROW

    async def test_inserts_expected_payload(self):
        client = make_supabase_client([_JOB_ROW])
        await insert_job_row(
            client,
            source="loopnet-seed",
            idempotency_key="loopnet-seed:2026-01-01",
        )
        client.table.return_value.insert.assert_called_once_with(
            {"source": "loopnet-seed", "idempotency_key": "loopnet-seed:2026-01-01"},
        )


class TestGetJobRow:
    _ID = UUID("6f1c2a9e-0000-4000-8000-0000000000aa")

    async def test_returns_the_row(self):
        client = make_supabase_client([_JOB_ROW])
        assert await get_job_row(client, self._ID) == _JOB_ROW
        client.table.return_value.eq.assert_called_once_with("id", str(self._ID))

    async def test_returns_none_when_missing(self):
        client = make_supabase_client([])
        assert await get_job_row(client, self._ID) is None
