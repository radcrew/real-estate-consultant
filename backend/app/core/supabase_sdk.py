import httpx
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings
from supabase import AsyncClient, acreate_client

_SUPABASE_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=15.0)

_supabase_client: AsyncClient | None = None
_supabase_http: httpx.AsyncClient | None = None


async def _create_client(api_key: str) -> tuple[AsyncClient, httpx.AsyncClient]:
    http = httpx.AsyncClient(
        timeout=_SUPABASE_HTTP_TIMEOUT,
        follow_redirects=True,
        http2=True,
    )
    client = await acreate_client(
        settings.supabase_url,
        api_key,
        options=AsyncClientOptions(
            httpx_client=http,
            # The server holds no user session; it only uses the service role.
            persist_session=False,
            auto_refresh_token=False,
        ),
    )
    return client, http


async def init_supabase() -> None:
    """Create the service-role client for PostgREST, Storage and the Auth admin API.

    User sign-in is handled by Cognito, so there is no anon client for password grants.
    """
    global _supabase_client, _supabase_http
    _supabase_client, _supabase_http = await _create_client(settings.supabase_service_role_key)
    # Ensure the data client Authorization header is the service role key.
    restore_service_role_auth_header()


async def close_supabase() -> None:
    global _supabase_client, _supabase_http
    if _supabase_http is not None:
        await _supabase_http.aclose()
    _supabase_client = None
    _supabase_http = None


async def check_supabase() -> bool:
    """Return True if the Supabase REST endpoint responds with a non-5xx status."""
    key = settings.supabase_service_role_key
    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            r = await client.get(
                f"{settings.supabase_url}/rest/v1/",
                headers={"apikey": key},
            )
        return r.status_code < 500
    except Exception:
        return False


def get_supabase_sdk_client() -> AsyncClient:
    """Service-role client for PostgREST / Auth Admin (never password sign-in)."""
    if _supabase_client is None:
        raise RuntimeError("Supabase client requested before init_supabase()")
    return _supabase_client


def restore_service_role_auth_header() -> None:
    """Reset data-client Authorization to the service role key (recovery helper)."""
    client = get_supabase_sdk_client()
    auth_header = f"Bearer {settings.supabase_service_role_key}"
    client.options.headers["Authorization"] = auth_header
    client.auth._headers["Authorization"] = auth_header
    client._postgrest = None
    client._storage = None
    client._functions = None
