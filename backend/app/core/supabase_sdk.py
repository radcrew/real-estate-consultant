from supabase import AsyncClient, acreate_client

from app.core.config import settings

SUPABASE_SDK_CLIENT: AsyncClient | None = None


async def get_supabase_sdk_client() -> AsyncClient:
    global SUPABASE_SDK_CLIENT
    
    if SUPABASE_SDK_CLIENT is None:
        SUPABASE_SDK_CLIENT = await acreate_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    
    return SUPABASE_SDK_CLIENT
