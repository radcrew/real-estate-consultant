"""Public-listing broker/agent profile: a broker and the listings they carry."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import DbSession
from app.models.properties import Properties
from app.repositories.properties import list_properties_by_broker
from app.schemas.listings import AgentProfileResponse
from app.utils.exceptions import raise_not_found

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get(
    "/{broker}",
    response_model=AgentProfileResponse,
    response_model_exclude_none=True,
    summary="Agent profile + their listings",
)
async def get_agent(broker: str, db: DbSession) -> AgentProfileResponse:
    rows = await list_properties_by_broker(db, broker)
    if not rows:
        raise_not_found("Agent not found.")

    first = rows[0]
    return AgentProfileResponse(
        name=first.get("listing_broker_name") or broker,
        email=first.get("listing_broker_email"),
        phone=first.get("listing_broker_phone"),
        properties=[Properties.model_validate(row) for row in rows],
    )
