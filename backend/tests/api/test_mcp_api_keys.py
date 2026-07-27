"""API tests for /api/v1/account/api-keys and dual auth (API key | JWT)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID

from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.supabase_sdk import get_supabase_auth_client, get_supabase_sdk_client
from app.main import create_app
from app.repositories.mcp_api_keys import ResolvedMcpApiKey

_UID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_KID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


def _make_auth_user(email: str = "user@example.com"):
    from supabase_auth.types import User

    return User(
        id=_UID,
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        email=email,
    )


def _resolved(*, scopes: list[str] | None = None) -> ResolvedMcpApiKey:
    return ResolvedMcpApiKey(
        user_id=UUID(_UID),
        key_id=UUID(_KID),
        key_prefix="rad_abcdefgh",
        scopes=scopes or ["*"],
    )


class TestMcpApiKeysCrud:
    async def test_create_returns_plaintext_once(self, client):
        meta = {
            "id": _KID,
            "user_id": _UID,
            "name": "Cursor",
            "key_prefix": "rad_abcdef",
            "scopes": ["*"],
            "created_at": "2026-07-27T00:00:00+00:00",
        }
        with patch(
            "app.api.v1.endpoints.account.api_keys.create_mcp_api_key",
            new_callable=AsyncMock,
            return_value=("rad_abcdefSECRET", meta),
        ) as create:
            r = await client.post(
                "/api/v1/account/api-keys",
                json={"name": "Cursor", "scopes": ["mcp:read"], "expires_in_days": 30},
            )
        assert r.status_code == 201
        body = r.json()
        assert body["api_key"] == "rad_abcdefSECRET"
        assert body["key_prefix"] == "rad_abcdef"
        assert body["name"] == "Cursor"
        assert "key_hash" not in body
        kwargs = create.await_args.kwargs
        assert kwargs["scopes"] == ["mcp:read"]
        assert kwargs["expires_at"] is not None

    async def test_create_rejects_bad_scopes(self, client):
        with patch(
            "app.api.v1.endpoints.account.api_keys.create_mcp_api_key",
            new_callable=AsyncMock,
            side_effect=ValueError("Unsupported MCP API key scopes: nope"),
        ):
            r = await client.post(
                "/api/v1/account/api-keys",
                json={"name": "bad", "scopes": ["nope"]},
            )
        assert r.status_code == 422

    async def test_list_keys(self, client):
        with patch(
            "app.api.v1.endpoints.account.api_keys.list_mcp_api_keys",
            new_callable=AsyncMock,
            return_value=[
                {
                    "id": _KID,
                    "name": "Cursor",
                    "key_prefix": "rad_abcdef",
                    "scopes": ["*"],
                    "created_at": "2026-07-27T00:00:00+00:00",
                    "last_used_at": None,
                    "revoked_at": None,
                    "expires_at": None,
                },
            ],
        ):
            r = await client.get("/api/v1/account/api-keys")
        assert r.status_code == 200
        keys = r.json()["keys"]
        assert len(keys) == 1
        assert keys[0]["id"] == _KID
        assert "api_key" not in keys[0]

    async def test_revoke_success(self, client):
        with patch(
            "app.api.v1.endpoints.account.api_keys.revoke_mcp_api_key",
            new_callable=AsyncMock,
            return_value={"id": _KID, "revoked_at": "2026-07-27T01:00:00+00:00"},
        ):
            r = await client.delete(f"/api/v1/account/api-keys/{_KID}")
        assert r.status_code == 204

    async def test_revoke_not_found(self, client):
        with patch(
            "app.api.v1.endpoints.account.api_keys.revoke_mcp_api_key",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.delete(f"/api/v1/account/api-keys/{_KID}")
        assert r.status_code == 404


class TestDualAuthApiKey:
    async def test_profile_with_x_api_key(self, mock_db, mock_supabase):
        """X-API-Key path resolves user without JWT get_user."""
        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_db
        app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
        app.dependency_overrides[get_supabase_auth_client] = lambda: mock_supabase

        auth_user = _make_auth_user()
        with (
            patch(
                "app.core.deps.resolve_mcp_api_key",
                new_callable=AsyncMock,
                return_value=_resolved(),
            ),
            patch(
                "app.core.deps.get_auth_user",
                new_callable=AsyncMock,
                return_value=auth_user,
            ),
            patch(
                "app.api.v1.endpoints.account.profile.get_profile_row",
                new_callable=AsyncMock,
                return_value={"id": _UID, "first_name": "Api"},
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as ac:
                r = await ac.get(
                    "/api/v1/account/profile",
                    headers={"X-API-Key": "rad_abcdefghijklmnop"},
                )
        assert r.status_code == 200
        assert r.json()["first_name"] == "Api"

    async def test_read_only_key_forbidden_on_post(self, mock_db, mock_supabase):
        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_db
        app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
        app.dependency_overrides[get_supabase_auth_client] = lambda: mock_supabase

        with patch(
            "app.core.deps.resolve_mcp_api_key",
            new_callable=AsyncMock,
            return_value=_resolved(scopes=["mcp:read"]),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as ac:
                r = await ac.post(
                    "/api/v1/account/api-keys",
                    headers={"X-API-Key": "rad_abcdefghijklmnop"},
                    json={"name": "x"},
                )
        assert r.status_code == 403
        assert "JWT" in r.json()["detail"]

    async def test_write_key_cannot_manage_keys(self, mock_db, mock_supabase):
        """Even mcp:write / * keys must not create, list, or revoke via API key auth."""
        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_db
        app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
        app.dependency_overrides[get_supabase_auth_client] = lambda: mock_supabase

        headers = {"Authorization": "Bearer rad_abcdefghijklmnop"}
        with patch(
            "app.core.deps.resolve_mcp_api_key",
            new_callable=AsyncMock,
            return_value=_resolved(scopes=["mcp:write"]),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as ac:
                create = await ac.post(
                    "/api/v1/account/api-keys",
                    headers=headers,
                    json={"name": "escalated", "scopes": ["*"]},
                )
                listed = await ac.get("/api/v1/account/api-keys", headers=headers)
                revoked = await ac.delete(
                    f"/api/v1/account/api-keys/{_KID}",
                    headers=headers,
                )
        assert create.status_code == 403
        assert listed.status_code == 403
        assert revoked.status_code == 403
        assert "JWT" in create.json()["detail"]

    async def test_invalid_api_key_returns_401(self, mock_db, mock_supabase):
        app = create_app()
        app.dependency_overrides[get_session] = lambda: mock_db
        app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
        app.dependency_overrides[get_supabase_auth_client] = lambda: mock_supabase

        with patch(
            "app.core.deps.resolve_mcp_api_key",
            new_callable=AsyncMock,
            return_value=None,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as ac:
                r = await ac.get(
                    "/api/v1/account/profile",
                    headers={"Authorization": "Bearer rad_abcdefghijklmnop"},
                )
        assert r.status_code == 401
