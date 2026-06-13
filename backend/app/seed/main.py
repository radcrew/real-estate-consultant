"""Load ``dataset/raw-data.json`` and upsert into Supabase ``public.properties`` (+ images).

Run from the ``backend/`` directory (same folder as ``pyproject.toml``)::

    python -m app.seed.main
"""

from __future__ import annotations

import asyncio
import logging
import sys
import time

from supabase import acreate_client

from app.core.config import settings
from app.core.db_safe import SupabaseRequestError
from app.core.logging import configure_logging
from app.seed.insert import SeedManager
from app.seed.parse import load_property_dataset

configure_logging(settings.log_level)
logger = logging.getLogger("seed")


async def run_seed() -> None:
    start = time.perf_counter()
    rows, report = load_property_dataset()
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

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "ingestion_run",
        extra={
            "source": "seed:dataset/raw-data.json",
            "fetched": report.fetched,
            "normalized": report.normalized,
            "rejected": report.rejected,
            "rejected_reasons": report.rejected_reasons,
            "inserted_properties": inserted,
            "inserted_images": inserted_images,
            "duration_ms": round(duration_ms, 2),
        },
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
