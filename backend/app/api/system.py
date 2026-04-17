import logging

import httpx
from fastapi import APIRouter, HTTPException
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse_dataset import load_properties
from app.seed.supabase_properties import insert_properties

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.is_dev_mode:

    @router.post("/seed", response_model=SeedDatasetResponse)
    async def seed_dataset(client: SupabaseSdkDep) -> SeedDatasetResponse:
        """Parse `dataset/raw-data.json` and insert rows into Supabase ``public.properties``."""
        logger.info("Seed: started (load dataset + insert into public.properties)")

        try:
            rows = load_properties()
        except FileNotFoundError as exc:
            logger.warning("Seed: dataset file missing (%s)", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            logger.warning("Seed: invalid dataset (%s)", exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        logger.info("Seed: parsed %d property row(s)", len(rows))

        sample_address: str | None = None
        if rows:
            sample_address = rows[0].address

        try:
            inserted = await insert_properties(client, rows)
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

        logger.info(
            "Seed: finished OK (record_count=%d, inserted_count=%d, sample_address=%r)",
            len(rows),
            inserted,
            sample_address,
        )

        return SeedDatasetResponse(
            ok=True,
            record_count=len(rows),
            inserted_count=inserted,
            sample_address=sample_address,
            message="Dataset parsed and inserted into public.properties.",
        )
