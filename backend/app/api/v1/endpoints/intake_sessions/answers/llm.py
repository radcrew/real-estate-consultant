"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import SupabaseSdkDep
from app.core.intake_admission import AdmitIntakeLlmTurn
from app.schemas.intake_sessions import (
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
)
from app.services.intake_llm import run_llm_intake_turn

router = APIRouter()


@router.post(
    "/llm",
    response_model=SubmitLlmIntakeInputResponse,
    # Anonymous and metered per request: without this, one caller can spend the provider
    # budget unattended — and once turns are queued, keep spending from the backlog.
    dependencies=[AdmitIntakeLlmTurn],
)
async def submit_llm_intake_input(
    session_id: UUID,
    body: SubmitLlmIntakeInputRequest,
    client: SupabaseSdkDep,
) -> SubmitLlmIntakeInputResponse:
    # The pipeline lives in the service so the queued worker runs the same code (§14.1).
    return await run_llm_intake_turn(client, session_id=session_id, user_input=body.input)
