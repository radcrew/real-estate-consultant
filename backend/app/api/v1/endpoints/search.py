"""Property search (``public.properties``) from GET query parameters."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.properties_search import search_properties
from app.schemas.search import SearchPropertiesResponse

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchPropertiesResponse,
    summary="Search properties using query parameters",
)
async def search_listings(
    client: SupabaseSdkDep,
    kind: str | None = Query(
        None,
        alias="type",
        description="Property type (maps to ``property_type``).",
    ),
    location: str | None = Query(
        None,
        description="Location text (matches city, state, address, country).",
    ),
    min_price: float | None = Query(None, alias="minPrice"),
    max_price: float | None = Query(None, alias="maxPrice"),
    min_size: float | None = Query(None, alias="minSize"),
    max_size: float | None = Query(None, alias="maxSize"),
    limit: int = Query(50, ge=1, le=100, description="Page size (max 100)."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> SearchPropertiesResponse:
    """Example: ``/api/v1/search?type=industrial&location=Canada&minPrice=100&maxPrice=100``."""
    criteria = {
        "type": kind,
        "location": location,
        "minPrice": min_price,
        "maxPrice": max_price,
        "minSize": min_size,
        "maxSize": max_size,
    }
    rows, total = await search_properties(client, criteria, limit=limit, offset=offset)
    results = [Properties.model_validate(row) for row in rows]
    return SearchPropertiesResponse(
        criteria=criteria,
        results=results,
        total=total,
        limit=limit,
        offset=offset,
    )
