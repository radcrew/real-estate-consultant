"""Similar-listings orchestration: embed seed + candidates, rank by cosine similarity."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.similarity import cosine_similarity, similarity_to_match_score
from app.llm.fit.prompts import format_listing_block_for_fit
from app.llm.providers.embeddings import embed
from app.repositories.properties import get_property_by_id, list_similar_candidate_rows

DEFAULT_RESULT_LIMIT = 6
DEFAULT_CANDIDATE_POOL = 40


async def find_similar_listings(
    session: AsyncSession,
    property_id: UUID,
    *,
    limit: int = DEFAULT_RESULT_LIMIT,
    candidate_pool: int = DEFAULT_CANDIDATE_POOL,
) -> list[tuple[dict[str, Any], float]] | None:
    """Return ranked similar listings as ``(row, match_score 0–100)``, or ``None`` if seed missing.

    Raises the embeddings provider's HTTP errors when no LLM keys are configured.
    """
    seed = await get_property_by_id(session, property_id)
    if seed is None:
        return None

    result_limit = max(0, min(limit, 20))
    pool_limit = max(result_limit, min(candidate_pool, 100))
    if result_limit == 0:
        return []

    candidates = await list_similar_candidate_rows(
        session,
        seed_id=property_id,
        state=seed.get("state") if isinstance(seed.get("state"), str) else None,
        city=seed.get("city") if isinstance(seed.get("city"), str) else None,
        property_type=(
            seed.get("property_type") if isinstance(seed.get("property_type"), str) else None
        ),
        limit=pool_limit,
    )
    if not candidates:
        return []

    texts = [format_listing_block_for_fit(seed)] + [
        format_listing_block_for_fit(row) for row in candidates
    ]
    vectors = await embed(texts=texts)
    if len(vectors) != len(texts):
        return []

    seed_vector = vectors[0]
    ranked: list[tuple[dict[str, Any], float]] = []
    for row, vector in zip(candidates, vectors[1:], strict=True):
        score = similarity_to_match_score(cosine_similarity(seed_vector, vector))
        ranked.append((row, score))

    ranked.sort(key=lambda item: (-item[1], str(item[0].get("id", ""))))
    return ranked[:result_limit]
