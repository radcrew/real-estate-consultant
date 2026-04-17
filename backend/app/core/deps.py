from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient

from app.core.database import get_session
from app.core.supabase_sdk import get_supabase_sdk_client

DbSession = Annotated[AsyncSession, Depends(get_session)]

SupabaseSdkDep = Annotated[AsyncClient, Depends(get_supabase_sdk_client)]
