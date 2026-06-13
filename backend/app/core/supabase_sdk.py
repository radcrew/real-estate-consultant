import httpx
from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings

_SUPABASE_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=15.0)

_supabase_client: AsyncClient | None = None
_supabase_http: httpx.AsyncClient | None = None


async def init_supabase() -> None:
    global _supabase_client, _supabase_http
    _supabase_http = httpx.AsyncClient(
        timeout=_SUPABASE_HTTP_TIMEOUT,
        follow_redirects=True,
        http2=True,
    )
    _supabase_client = await acreate_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=AsyncClientOptions(httpx_client=_supabase_http),
    )


async def close_supabase() -> None:
    global _supabase_client, _supabase_http
    if _supabase_http is not None:
        await _supabase_http.aclose()
    _supabase_client = None
    _supabase_http = None


async def check_supabase() -> bool:
    """Return True if the Supabase REST endpoint responds with a non-5xx status."""
    key = settings.supabase_anon_key or settings.supabase_service_role_key
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                f"{settings.supabase_url}/rest/v1/",
                headers={"apikey": key},
            )
        return r.status_code < 500
    except Exception:
        return False


def get_supabase_sdk_client() -> AsyncClient:
    if _supabase_client is None:
        raise RuntimeError("Supabase client requested before init_supabase()")
    return _supabase_client
