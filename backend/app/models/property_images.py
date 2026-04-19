from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel


class PropertyImages(BaseModel):

    property_id: UUID
    url: str
