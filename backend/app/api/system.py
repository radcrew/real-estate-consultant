import logging
from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse import load_property_dataset
from app.seed.insert import (
    delete_property_images_for_property_ids,
    insert_properties,
    insert_property_images,
)

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

        properties_payload = [prop for prop, _ in rows]
        property_ids = [str(p.id) for p in properties_payload if p.id is not None]
        await delete_property_images_for_property_ids(client, property_ids)

        inserted = await insert_properties(client, properties_payload)

        image_rows: list[dict[str, Any]] = []
        for _, images in rows:
            for img in images:
                image_rows.append(img.model_dump(mode="json"))

        inserted_images = await insert_property_images(client, image_rows)

        first_address = rows[0][0].address if rows else None

        logger.info(
            "Seed: finished OK (record_count=%d, inserted_count=%d, images=%d, first_address=%r)",
            len(rows),
            inserted,
            inserted_images,
            first_address,
        )

        return SeedDatasetResponse(
            ok=True,
            record_count=len(rows),
            inserted_count=inserted,
            inserted_image_count=inserted_images,
            message=(
                "Dataset upserted into public.properties; property_images replaced for those ids."
            ),
        )
