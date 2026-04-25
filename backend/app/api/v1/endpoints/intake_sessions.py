"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

import re
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.repositories.intake_sessions import (
    append_intake_criteria_answer,
    create_intake_session_row,
    load_intake_session_row,
    parse_intake_session,
    update_intake_session_after_answers,
    update_intake_session_completed,
)
from app.repositories.questions import (
    load_first_intake_question,
    load_intake_questions,
    map_question_to_model,
    next_question_row_after_order,
    order_for_question_key,
)
from app.repositories.search_profiles import (
    create_search_profile,
    ensure_search_profile_access,
)
from app.schemas.intake_sessions import (
    CreateIntakeSessionResponse,
    CreateIntakeSessionResponseGuided,
    CreateIntakeSessionResponseLlm,
    LlmExtractedIntakePayload,
    LlmExtractedLocation,
    LlmExtractedRange,
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)

LLM_INTAKE_OPENING_MESSAGE = (
    "Hi! I'm here to help you find the right commercial property. "
    "Tell me what you're looking for — be as detailed or brief as you want. "
    'For example: "I need a 100k sqft industrial warehouse with 32ft clear '
    'height in Chicago for lease, with at least 20 dock doors."'
)

router = APIRouter(tags=["intake-sessions"])

_KNOWN_LOCATIONS: dict[str, tuple[str, float, float]] = {
    "dallas": ("Dallas, TX", 32.7767, -96.7970),
    "chicago": ("Chicago, IL", 41.8781, -87.6298),
    "los angeles": ("Los Angeles, CA", 34.0522, -118.2437),
    "new york": ("New York, NY", 40.7128, -74.0060),
}
_REQUIRED_LLM_FIELDS: tuple[str, ...] = ("building_type", "location", "radius_miles", "listing_type")


def _extract_llm_payload(text: str) -> LlmExtractedIntakePayload:
    lower = text.lower()
    building_type: list[str] | None = None
    if "warehouse" in lower or "industrial" in lower:
        building_type = ["industrial"]
    elif "office" in lower:
        building_type = ["office"]
    elif "retail" in lower:
        building_type = ["retail"]

    location: LlmExtractedLocation | None = None
    for key, (label, lat, lng) in _KNOWN_LOCATIONS.items():
        if key in lower:
            location = LlmExtractedLocation(label=label, lat=lat, lng=lng)
            break

    size_sqft: LlmExtractedRange | None = None
    size_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(k|m)?\s*(?:sq\s*ft|sqft|sf)\b", lower)
    if size_match:
        base = float(size_match.group(1).replace(",", ""))
        suffix = size_match.group(2)
        if suffix == "k":
            base *= 1000
        elif suffix == "m":
            base *= 1_000_000
        size_sqft = LlmExtractedRange(min=max(0.0, base - 500), max=base + 500)

    rent_range: LlmExtractedRange | None = None
    rent_match = re.search(r"(?:under|below|max(?:imum)?|up to)\s*\$?\s*(\d+(?:[.,]\d+)?)(k)?", lower)
    if rent_match:
        amount = float(rent_match.group(1).replace(",", ""))
        if rent_match.group(2) == "k":
            amount *= 1000
        rent_range = LlmExtractedRange(max=amount)

    return LlmExtractedIntakePayload(
        building_type=building_type,
        location=location,
        size_sqft=size_sqft,
        rent_range=rent_range,
    )


@router.post(
    "/intake-sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateIntakeSessionResponse,
)
async def create_intake_session(
    client: SupabaseSdkDep,
    mode: Literal["llm", "guided"] = Query(
        "guided",
        description='Intake style: "guided" uses the questionnaire; "llm" returns an open prompt.',
    ),
) -> CreateIntakeSessionResponse:
    """Create an intake session. Guided mode returns the first question; LLM mode returns a welcome message."""
    created_session = await create_intake_session_row(client)
    validated_session = parse_intake_session(created_session)

    if validated_session.id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )

    if mode == "llm":
        return CreateIntakeSessionResponseLlm(
            mode="llm",
            session_id=validated_session.id,
            status=validated_session.status,
            message=LLM_INTAKE_OPENING_MESSAGE,
        )

    first_question = await load_first_intake_question(client)
    return CreateIntakeSessionResponseGuided(
        mode="guided",
        session_id=validated_session.id,
        status=validated_session.status,
        first_question=first_question,
    )


@router.get(
    "/intake-sessions/{session_id}",
    response_model=IntakeSession,
)
async def get_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    """Return one session only if its linked search profile belongs to the caller."""
    session_row = await load_intake_session_row(client, session_id)
    await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    return parse_intake_session(session_row)


@router.patch(
    "/intake-sessions/{session_id}/answers",
    response_model=UpdateIntakeSessionAnswersResponse,
)
async def submit_intake_session_answers(
    session_id: UUID,
    body: UpdateIntakeSessionAnswersRequest,
    client: SupabaseSdkDep,
) -> UpdateIntakeSessionAnswersResponse:
    answer_key = body.key.strip()
    session_row = await load_intake_session_row(client, session_id)
    questions = await load_intake_questions(client)

    merged_criteria = append_intake_criteria_answer(
        session_row.get("criteria"),
        answer_key,
        body.answers,
    )

    answered_order = order_for_question_key(questions, answer_key)
    if answered_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown question key for this questionnaire.",
        )

    next_row = next_question_row_after_order(questions, after_order=answered_order)
    next_question = map_question_to_model(next_row) if next_row is not None else None

    row = await update_intake_session_after_answers(
        client,
        session_id,
        merged_criteria,
    )
    return UpdateIntakeSessionAnswersResponse(
        session=parse_intake_session(row),
        next_question=next_question,
    )


@router.post(
    "/intake-sessions/{session_id}/llm-input",
    response_model=SubmitLlmIntakeInputResponse,
)
async def submit_llm_intake_input(
    session_id: UUID,
    body: SubmitLlmIntakeInputRequest,
    client: SupabaseSdkDep,
) -> SubmitLlmIntakeInputResponse:
    session_row = await load_intake_session_row(client, session_id)
    questions = await load_intake_questions(client)
    extracted = _extract_llm_payload(body.input)

    current_criteria = session_row.get("criteria")
    merged_criteria = dict(current_criteria) if isinstance(current_criteria, dict) else {}
    extracted_dict = extracted.model_dump(exclude_none=True)
    merged_criteria.update(extracted_dict)

    missing_fields = [key for key in _REQUIRED_LLM_FIELDS if key not in merged_criteria]

    next_question = None
    for q in questions:
        qkey = q.get("key")
        if isinstance(qkey, str) and qkey in missing_fields:
            next_question = map_question_to_model(q)
            break

    await update_intake_session_after_answers(client, session_id, merged_criteria)
    return SubmitLlmIntakeInputResponse(
        extracted=extracted,
        criteria=merged_criteria,
        missing_fields=missing_fields,
        next_question=next_question,
        is_complete=len(missing_fields) == 0,
    )


@router.post(
    "/intake-sessions/{session_id}/complete",
    response_model=IntakeSession,
)
async def complete_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    session_row = await load_intake_session_row(client, session_id)
    search_profile_id = await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    if search_profile_id is None:
        search_profile_id = await create_search_profile(client, current_user.id)

    updated_row = await update_intake_session_completed(
        client,
        session_id,
        search_profile_id,
    )
    return parse_intake_session(updated_row)
