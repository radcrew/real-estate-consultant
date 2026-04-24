from supabase import AsyncClient, acreate_client

from app.core.config import settings

async def get_supabase_sdk_client() -> AsyncClient:
    # Important: return a fresh client per request.
    # Supabase auth calls can mutate in-memory auth state; sharing one global client
    # across requests may leak user session state into unrelated DB operations.
    return await acreate_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
