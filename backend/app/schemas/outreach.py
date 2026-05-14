"""API schemas for broker outreach drafts (``public.outreach_drafts``)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateOutreachDraftRequest(BaseModel):
    property_id: UUID


class OutreachDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    property_id: UUID | None = None
    user_id: UUID | None = None
    draft_email: str | None = None
    created_at: datetime | None = None


class PatchOutreachDraftRequest(BaseModel):
    draft_email: str = Field(min_length=1, max_length=32000)
