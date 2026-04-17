from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.seed import SeedDatasetResponse
from app.seed.parse_dataset import load_properties

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if settings.is_dev_mode:

    @router.post("/seed", response_model=SeedDatasetResponse)
    def seed_dataset() -> SeedDatasetResponse:
        """Load and validate `dataset/raw-data.json` (Supabase insert comes later)."""
        try:
            rows = load_properties()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        sample_address: str | None = None
        if rows:
            sample_address = rows[0].address

        return SeedDatasetResponse(
            ok=True,
            record_count=len(rows),
            sample_address=sample_address,
            message="Dataset parsed into Properties rows; database seeding not implemented yet.",
        )
