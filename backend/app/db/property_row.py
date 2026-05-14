"""ORM mapping for ``public.properties``."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


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
