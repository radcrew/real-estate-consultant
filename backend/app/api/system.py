import logging

from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse import load_property_dataset
from app.seed.insert import insert_properties

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.is_dev_mode:

    @router.post("/seed", response_model=SeedDatasetResponse)
    async def seed_dataset(client: SupabaseSdkDep) -> SeedDatasetResponse:
        logger.info("Seed: started (load dataset + insert into public.properties)")

        rows = load_property_dataset()

        logger.info("Seed: parsed %d property row(s)", len(rows))

        inserted = await insert_properties(client, rows)

        logger.info(
            "Seed: finished OK (record_count=%d, inserted_count=%d, first_address=%r)",
            len(rows),
            inserted,
            rows[0].address if rows else None,
        )

        return SeedDatasetResponse(
            ok=True,
            record_count=len(rows),
            inserted_count=inserted,
            message="Dataset parsed and inserted into public.properties.",
        )
