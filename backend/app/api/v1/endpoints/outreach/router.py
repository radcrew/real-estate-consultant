"""Broker outreach drafts: generate (POST), read (GET), edit (PATCH)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.v1.endpoints.listings.exceptions import raise_listing_not_found
from app.api.v1.endpoints.outreach.exceptions import raise_outreach_draft_not_found
from app.core.deps import CurrentUser, DbSession, SupabaseSdkDep
from app.llm.outreach.service import generate_broker_outreach_draft
from app.repositories.outreach_drafts import (
    fetch_latest_outreach_draft_for_property,
    fetch_outreach_draft_for_user,
    insert_outreach_draft,
    update_outreach_draft_email,
)
from app.repositories.profiles import fetch_profile_row
from app.repositories.properties import get_property_by_id
from app.schemas.outreach import (
    CreateOutreachDraftRequest,
    OutreachDraftResponse,
    PatchOutreachDraftRequest,
)

router = APIRouter(prefix="/outreach", tags=["outreach"])


@router.post(
    "/drafts",
    response_model=OutreachDraftResponse,
    response_model_exclude_none=True,
    summary="Generate and save an outreach draft",
)
async def create_outreach_draft(
    body: CreateOutreachDraftRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
    db: DbSession,
) -> OutreachDraftResponse:
    user_id = UUID(current_user.id)
    row = await get_property_by_id(db, body.property_id)
    if row is None:
        raise_listing_not_found()

    profile = await fetch_profile_row(client, user_id)
    auth_email = getattr(current_user, "email", None)
    if isinstance(auth_email, str):
        auth_email = auth_email.strip() or None
    else:
        auth_email = None

    draft_text = await generate_broker_outreach_draft(
        property_row=row,
        profile_row=profile,
        auth_email=auth_email,
    )
    saved = await insert_outreach_draft(
        client,
        user_id=user_id,
        property_id=body.property_id,
        draft_email=draft_text,
    )
    return OutreachDraftResponse.model_validate(saved)


@router.get(
    "/drafts/latest",
    response_model=OutreachDraftResponse,
    response_model_exclude_none=True,
    summary="Latest saved draft for a property (current user)",
)
async def get_latest_outreach_draft_for_property(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
    property_id: UUID = Query(..., description="Property UUID"),
) -> OutreachDraftResponse:
    user_id = UUID(current_user.id)
    found = await fetch_latest_outreach_draft_for_property(
        client,
        user_id=user_id,
        property_id=property_id,
    )
    if found is None:
        raise_outreach_draft_not_found()
    return OutreachDraftResponse.model_validate(found)


@router.get(
    "/drafts/{draft_id}",
    response_model=OutreachDraftResponse,
    response_model_exclude_none=True,
    summary="Get one outreach draft by id",
)
async def get_outreach_draft(
    draft_id: UUID,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> OutreachDraftResponse:
    user_id = UUID(current_user.id)
    found = await fetch_outreach_draft_for_user(client, draft_id=draft_id, user_id=user_id)
    if found is None:
        raise_outreach_draft_not_found()
    return OutreachDraftResponse.model_validate(found)


@router.patch(
    "/drafts/{draft_id}",
    response_model=OutreachDraftResponse,
    response_model_exclude_none=True,
    summary="Update draft email text",
)
async def patch_outreach_draft(
    draft_id: UUID,
    body: PatchOutreachDraftRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> OutreachDraftResponse:
    user_id = UUID(current_user.id)
    updated = await update_outreach_draft_email(
        client,
        draft_id=draft_id,
        user_id=user_id,
        draft_email=body.draft_email,
    )
    if updated is None:
        raise_outreach_draft_not_found()
    return OutreachDraftResponse.model_validate(updated)
