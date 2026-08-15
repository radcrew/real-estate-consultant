"""Similar-listings orchestration: embed the seed, rank by indexed cosine distance."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.similarity import similarity_to_match_score
from app.llm.fit.prompts import format_listing_block_for_fit
from app.llm.providers.embeddings import embed
from app.llm.providers.routing import resolve_embeddings_model_id
from app.repositories.properties import (
    get_property_by_id,
    get_property_embedding,
    list_similar_by_embedding,
)

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

    # The seed is itself an ingested listing, so its vector is already stored — and the
    # backfill built it from this exact text. Re-embedding would pay a provider per
    # request to recompute a value the row is holding, on a public endpoint where the
    # caller decides how often that happens.
    seed_vector = await get_property_embedding(
        session, property_id, model=resolve_embeddings_model_id()
    )
    if seed_vector is None:
        # Not backfilled yet, or carrying a superseded model's vector. Embedding here
        # keeps the endpoint working during a migration instead of returning nothing.
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
    # the same.
    if state and len(ranked) < result_limit:
        ranked += await list_similar_by_embedding(
            session,
            seed_id=property_id,
            embedding=seed_vector,
            exclude_ids=[row["id"] for row, _ in ranked],
            limit=result_limit - len(ranked),
        )

    scored = [(row, similarity_to_match_score(similarity)) for row, similarity in ranked]
    # State scopes which rows are eligible, not how they rank: the two queries are each
    # sorted, but concatenating them can put a weaker in-state match above a stronger
    # out-of-state one. Sort by score so the list a user sees never goes back up.
    scored.sort(key=lambda item: (-item[1], str(item[0].get("id", ""))))
    return scored
