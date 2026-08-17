"""Populate listing embeddings so similar-listings search has vectors to rank."""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.fit.prompts import format_listing_block_for_fit
from app.llm.providers.embeddings import embed
from app.llm.providers.routing import resolve_embeddings_model_id
from app.repositories.properties import (
    list_properties_needing_embedding,
    set_property_embedding,
)
from app.utils.exceptions import raise_bad_gateway

DEFAULT_BATCH_SIZE = 50

logger = logging.getLogger(__name__)


async def backfill_listing_embeddings(
    session: AsyncSession,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_batches: int | None = None,
) -> int:
    """Embed every listing that has no vector, or one from a superseded model.

    Returns the number of listings embedded. Each batch is committed before the next is
    selected, so an interrupted run resumes where it stopped rather than starting over —
    rows are re-selected only while they still lack a current-model vector.

    ``max_batches`` bounds a single run, for a scheduled job that should not hold a
    connection open across an entire corpus.
    """
    model = resolve_embeddings_model_id()
    written = 0
    batches = 0

    while max_batches is None or batches < max_batches:
        rows = await list_properties_needing_embedding(session, model=model, limit=batch_size)
        if not rows:
            break

        vectors = await embed(texts=[format_listing_block_for_fit(row) for row in rows])
        if len(vectors) != len(rows):
            # Positional zip below would mis-assign vectors to listings.
            raise_bad_gateway(
                "The embedding provider returned a different number of vectors than listings.",
            )

        for row, vector in zip(rows, vectors, strict=True):
            await set_property_embedding(
                session,
                property_id=row["id"],
                embedding=vector,
                model=model,
            )
        await session.commit()

        written += len(rows)
        batches += 1
        logger.info(
            "listing_embeddings_batch",
            extra={"model": model, "batch_size": len(rows), "written_total": written},
        )

    return written
