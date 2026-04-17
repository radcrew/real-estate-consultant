from fastapi import APIRouter, HTTPException

from app.schemas.seed import SeedDatasetResponse
from app.seed.loopnet_raw import load_listings

router = APIRouter(tags=["seed"])


@router.post("/seed", response_model=SeedDatasetResponse)
def seed_dataset() -> SeedDatasetResponse:
    """Load and validate `dataset/raw-data.json` (Supabase insert comes later)."""
    try:
        records = load_listings()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    sample: str | None = None
    if records:
        raw = records[0].get("propertyId")
        sample = str(raw) if raw is not None else None

    return SeedDatasetResponse(
        ok=True,
        record_count=len(records),
        sample_property_id=sample,
        message="Dataset loaded and validated; database seeding not implemented yet.",
    )
