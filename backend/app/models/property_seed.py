from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.properties import Properties


class PropertySeedBundle(BaseModel):
    """One listing: normalized property row plus Apify KV image URLs for seeding."""

    property: Properties
    kv_image_urls: list[str] = Field(default_factory=list)
