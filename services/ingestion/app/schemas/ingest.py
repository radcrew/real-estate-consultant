from pydantic import BaseModel


class IngestRequest(BaseModel):
    source: str = "loopnet-seed"


class IngestResponse(BaseModel):
    source: str
    fetched: int
    normalized: int
    rejected: int
    rejected_reasons: dict[str, int]
    duration_ms: float
