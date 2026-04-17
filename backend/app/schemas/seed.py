from pydantic import BaseModel


class SeedDatasetResponse(BaseModel):
    ok: bool
    record_count: int
    sample_address: str | None = None
    message: str
