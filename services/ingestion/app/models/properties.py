"""Normalized listing row extracted from LoopNet-style raw JSON."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class Properties(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    property_type: str | None = None
    listing_type: str | None = None
    description: str | None = None
    size_sqft: float | None = None
    price: float | None = None
    rent: float | None = None

    clear_height: float | None = None
    loading_docks: int | None = None

    listing_broker_name: str | None = None
    listing_broker_email: str | None = None
    listing_broker_phone: str | None = None

    image: str | None = None
