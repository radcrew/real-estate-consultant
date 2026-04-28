import httpx
from supabase import AsyncClient, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings

# Without a custom client, supabase-auth uses httpx's default timeouts (~5s), which
# often surfaces as intermittent ConnectTimeout on slow DNS/TLS or busy networks.
_SUPABASE_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=15.0)


async def get_supabase_sdk_client() -> AsyncClient:
    # Important: return a fresh client per request.
    # Supabase auth calls can mutate in-memory auth state; sharing one global client
    # across requests may leak user session state into unrelated DB operations.
    http = httpx.AsyncClient(
        timeout=_SUPABASE_HTTP_TIMEOUT,
        follow_redirects=True,
        http2=True,
    )
    return await acreate_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=AsyncClientOptions(httpx_client=http),
    )
