"""ORM mapping for ``public.properties``."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Cohere Embed v3 on Bedrock. Fixed because HNSW needs a constant width and a stored
# vector is only comparable against others from the same model.
EMBEDDING_DIMENSIONS = 1024


class PropertyRow(Base):
    __tablename__ = "properties"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    property_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_sqft: Mapped[float | None] = mapped_column(Float, nullable=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    rent: Mapped[float | None] = mapped_column(Float, nullable=True)
    clear_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    loading_docks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    listing_broker_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_broker_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    listing_broker_phone: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Written once at ingest, not per request. embedding_model makes rows produced by a
    # superseded model findable so a re-embed can target only what is stale.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
