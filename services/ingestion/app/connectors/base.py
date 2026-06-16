from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class IngestionReport:
    """Summary returned by every connector after a run."""

    source: str
    fetched: int
    normalized: int
    rejected_reasons: dict[str, int] = field(default_factory=dict)

    @property
    def rejected(self) -> int:
        return self.fetched - self.normalized


class ConnectorBase(ABC):
    """All listing connectors implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique connector identifier used as the job source name."""

    @abstractmethod
    async def run(self) -> IngestionReport:
        """Fetch, normalize, and persist listings. Returns a summary report."""
