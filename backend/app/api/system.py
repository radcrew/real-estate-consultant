import logging

from fastapi import APIRouter

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse import load_property_dataset
from app.seed.insert import insert_properties, insert_property_images

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.is_dev_mode:

    @router.post("/seed", response_model=SeedDatasetResponse)
    async def seed_dataset(client: SupabaseSdkDep) -> SeedDatasetResponse:
        logger.info("Seed: started (load dataset + insert into public.properties)")

        bundles = load_property_dataset()

        logger.info("Seed: parsed %d property row(s)", len(bundles))

        properties_payload = [b.property for b in bundles]
        inserted = await insert_properties(client, properties_payload)

        image_rows: list[dict[str, str | int]] = []
        for bundle in bundles:
            prop_id = bundle.property.id
            if prop_id is None:
                continue
            pid_str = str(prop_id)
            for position, url in enumerate(bundle.kv_image_urls):
                image_rows.append(
                    {"property_id": pid_str, "url": url, "position": position},
                )

        inserted_images = await insert_property_images(client, image_rows)

        first_address = bundles[0].property.address if bundles else None

        logger.info(
            "Seed: finished OK (record_count=%d, inserted_count=%d, images=%d, first_address=%r)",
            len(bundles),
            inserted,
            inserted_images,
            first_address,
        )

        return SeedDatasetResponse(
            ok=True,
            record_count=len(bundles),
            inserted_count=inserted,
            inserted_image_count=inserted_images,
            message="Dataset parsed and inserted into public.properties and public.property_images.",
        )
