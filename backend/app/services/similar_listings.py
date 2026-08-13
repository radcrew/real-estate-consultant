"""Similar-listings orchestration: embed the seed, rank by indexed cosine distance."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.similarity import similarity_to_match_score
from app.llm.fit.prompts import format_listing_block_for_fit
from app.llm.providers.embeddings import embed
from app.repositories.properties import get_property_by_id, list_similar_by_embedding

DEFAULT_RESULT_LIMIT = 6
MAX_RESULT_LIMIT = 20


async def find_similar_listings(
    session: AsyncSession,
    property_id: UUID,
    *,
    limit: int = DEFAULT_RESULT_LIMIT,
) -> list[tuple[dict[str, Any], float]] | None:
    """Return ranked similar listings as ``(row, match_score 0–100)``, or ``None`` if seed missing.

    Listings are embedded once at ingest, so only the seed is embedded here — one
    provider call regardless of how many candidates exist. Ranking is an indexed k-NN
    query over the whole corpus rather than a Python scan of a pre-filtered pool.

    Raises the embeddings provider's HTTP errors when no LLM keys are configured.
    """
    seed = await get_property_by_id(session, property_id)
    if seed is None:
        return None

    result_limit = max(0, min(limit, MAX_RESULT_LIMIT))
    if result_limit == 0:
        return []

    vectors = await embed(texts=[format_listing_block_for_fit(seed)])
    if not vectors:
        return []
    seed_vector = vectors[0]

    state = seed.get("state") if isinstance(seed.get("state"), str) else None
    ranked = await list_similar_by_embedding(
        session,
        seed_id=property_id,
        embedding=seed_vector,
        state=state,
        limit=result_limit,
    )

    # Sparse region: the previous implementation preferred same-state rows but filled the
    # pool from elsewhere rather than returning short, so widen once to keep result counts
    # the same. Same-state matches still rank first, because they were selected first.
    if state and len(ranked) < result_limit:
        ranked += await list_similar_by_embedding(
            session,
            seed_id=property_id,
            embedding=seed_vector,
            exclude_ids=[row["id"] for row, _ in ranked],
            limit=result_limit - len(ranked),
        )

    return [(row, similarity_to_match_score(similarity)) for row, similarity in ranked]
