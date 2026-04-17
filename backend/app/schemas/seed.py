from pydantic import BaseModel


class SeedDatasetResponse(BaseModel):
    ok: bool
    record_count: int
    upserted_count: int = 0
    sample_address: str | None = None
    message: str
