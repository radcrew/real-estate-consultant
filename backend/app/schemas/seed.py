from pydantic import BaseModel


class SeedDatasetResponse(BaseModel):
    ok: bool
    record_count: int
    inserted_count: int = 0
    inserted_image_count: int = 0
    message: str
