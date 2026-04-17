from pydantic import BaseModel


class SeedDatasetResponse(BaseModel):
    ok: bool
    record_count: int
    sample_property_id: str | None = None
    message: str
