from fastapi import APIRouter, HTTPException
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse_dataset import load_properties
from app.seed.supabase_properties import upsert_properties
router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.is_dev_mode:

    @router.post("/seed", response_model=SeedDatasetResponse)
    async def seed_dataset(client: SupabaseSdkDep) -> SeedDatasetResponse:
        """Parse `dataset/raw-data.json` and upsert rows into Supabase ``public.properties``."""
        try:
            rows = load_properties()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        sample_address: str | None = None
        if rows:
            sample_address = rows[0].address

        try:
            upserted = await upsert_properties(client, rows)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except APIError as exc:
            raise HTTPException(status_code=502, detail=f"Supabase error: {exc}") from exc

        return SeedDatasetResponse(
            ok=True,
            record_count=len(rows),
            upserted_count=upserted,
            sample_address=sample_address,
            message="Dataset parsed and upserted into public.properties.",
        )
