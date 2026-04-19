"""Load ``dataset/raw-data.json`` and upsert into Supabase ``public.properties`` (+ images).

Run from the ``backend/`` directory (same folder as ``pyproject.toml``)::

    python -m app.seed.main
"""

from __future__ import annotations

import asyncio
import logging
import sys

from supabase import acreate_client

from app.core.config import settings
from app.core.db_safe import SupabaseRequestError
from app.seed.insert import SeedManager
from app.seed.parse import load_property_dataset

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("seed")


async def run_seed() -> None:
    rows = load_property_dataset()
    logger.info("Parsed %d property row(s)", len(rows))

    properties_payload = [prop for prop, _ in rows]
    property_ids = [str(p.id) for p in properties_payload if p.id is not None]

    client = await acreate_client(settings.supabase_url, settings.supabase_service_role_key)
    seed_manager = SeedManager(client)
    try:
        await seed_manager.delete_property_images(property_ids)
        inserted = await seed_manager.insert_properties(properties_payload)
        image_rows = [img.model_dump(mode="json") for _, images in rows for img in images]
        inserted_images = await seed_manager.insert_property_images(image_rows)
    finally:
        await client.postgrest.aclose()

    first_address = rows[0][0].address if rows else None
    logger.info(
        "Finished OK (record_count=%d, inserted_count=%d, images=%d, first_address=%r)",
        len(rows),
        inserted,
        inserted_images,
        first_address,
    )


def main() -> None:
    try:
        asyncio.run(run_seed())
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        sys.exit(1)
    except SupabaseRequestError as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
