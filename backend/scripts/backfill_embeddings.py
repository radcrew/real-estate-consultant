"""Backfill listing embeddings.

Run from ``backend/``::

    python scripts/backfill_embeddings.py --batch-size 50

Requires the embeddings route to point at a model whose width matches the
``properties.embedding`` column; a mismatch fails before anything is written.
"""

from __future__ import annotations

import argparse
import asyncio

from app.core import database
from app.services.listing_embeddings import DEFAULT_BATCH_SIZE, backfill_listing_embeddings


async def run(*, batch_size: int, max_batches: int | None) -> int:
    await database.init_db()
    try:
        session_maker = database.DB_ASYNC_SESSION_MAKER
        if session_maker is None:  # pragma: no cover - init_db always sets it
            raise RuntimeError("Database session maker was not initialised.")
        async with session_maker() as session:
            return await backfill_listing_embeddings(
                session,
                batch_size=batch_size,
                max_batches=max_batches,
            )
    finally:
        await database.close_db()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
        help="Stop after this many batches instead of draining the backlog.",
    )
    args = parser.parse_args()
    written = asyncio.run(run(batch_size=args.batch_size, max_batches=args.max_batches))
    print(f"Embedded {written} listing(s).")


if __name__ == "__main__":
    main()
