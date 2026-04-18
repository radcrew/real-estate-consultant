"""Insert parsed `Properties` rows into Supabase `public.properties`."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException
from postgrest.exceptions import APIError
from supabase import AsyncClient

from app.models.properties import Properties

logger = logging.getLogger(__name__)


async def insert_properties(client: AsyncClient, rows: list[Properties]) -> int:
    if not rows:
        logger.info("Supabase properties insert: no rows, skipping")
        return 0
    payload = [row.model_dump() for row in rows]
    logger.info("Supabase properties insert: inserting %d row(s)", len(payload))
    
    try:
        result = await client.table("properties").insert(payload).execute()
    
    except APIError as exc:
        logger.error("Seed: Supabase PostgREST error: %s", exc)
        err_text = str(exc).lower()
        if "pgrst204" in err_text or "schema cache" in err_text:
            logger.error(
                "Seed: hint - PostgREST schema cache stale or column missing. "
                "Apply migrations, then SQL Editor: NOTIFY pgrst, 'reload schema';"
            )
        raise HTTPException(status_code=502, detail=f"Supabase (PostgREST): {exc}") from exc
    
    except httpx.HTTPError as exc:
        logger.error("Seed: HTTP error talking to Supabase: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not reach Supabase (check SUPABASE_URL, network, and that the "
                f"project is running): {exc}"
            ),
        ) from exc
        
    if isinstance(result.data, list):
        n = len(result.data)
        logger.info("Supabase properties insert: PostgREST returned %d row(s)", n)
        return n
    
    logger.info(
        "Supabase properties insert: no row data in response, assuming %d sent",
        len(payload),
    )
    
    return len(payload)
