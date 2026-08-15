"""``chat-intake-worker``: runs queued intake turns off the FIFO queue.

Consumes ``chat-intake.fifo`` and calls the same pipeline the endpoint runs inline, so a
turn produces the same result whichever path it took.

Three rules carry the correctness of this handler:

1. **Claim before working.** SQS delivers at least once, so the ``queued -> running``
   claim is what stops a redelivered message from paying for a turn already completed.
2. **Classify failures.** Transient faults go back on the queue; deterministic ones stop.
   Backwards in one direction loses a turn the user could have had, and in the other
   burns quota re-earning the same error until the DLQ catches it.
3. **Preserve order on failure.** This is a FIFO queue, and a retried message must not be
   overtaken by the next turn of the same conversation — see ``process_batch``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.core.supabase_sdk import get_supabase_sdk_client, init_supabase
from app.repositories.intake_jobs import (
    claim_intake_job,
    complete_intake_job,
    fail_intake_job,
)
from app.services.intake_llm import run_llm_intake_turn
from supabase import AsyncClient

# The §8 raisers that mean "the provider was unreachable", as opposed to "the provider
# answered and the answer was unusable". Only these are worth a redelivery.
RETRYABLE_STATUS = frozenset({503, 504})

logger = logging.getLogger(__name__)

_initialised = False


async def get_client() -> AsyncClient:
    """Service-role client, created once per environment and reused while warm."""
    global _initialised
    if not _initialised:
        await init_supabase()
        _initialised = True
    return get_supabase_sdk_client()


def parse_record(record: dict[str, Any]) -> tuple[UUID, UUID] | None:
    """Read ``(job_id, session_id)`` from a message body, or ``None`` if unreadable."""
    try:
        body = json.loads(record.get("body") or "")
        return UUID(body["job_id"]), UUID(body["session_id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def group_of(record: dict[str, Any]) -> str:
    return str((record.get("attributes") or {}).get("MessageGroupId") or "")


async def process_record(client: AsyncClient, record: dict[str, Any]) -> bool:
    """Run one turn. Returns whether the message should be redelivered."""
    parsed = parse_record(record)
    if parsed is None:
        # Redelivery cannot fix a malformed body, so retrying only burns the receive
        # count on the way to the DLQ. The job row it referred to is unknown, which is
        # why the publisher writes the row first and sends only ids.
        logger.error("chat_job_unreadable_message", extra={"message_id": record.get("messageId")})
        return False

    job_id, session_id = parsed
    claimed = await claim_intake_job(client, job_id=job_id)
    if claimed is None:
        # Already running or finished: this is a redelivery of work someone else did.
        # Dropping it is the whole point of the claim gate.
        logger.info("chat_job_already_claimed", extra={"job_id": str(job_id)})
        return False

    try:
        response = await run_llm_intake_turn(
            client,
            session_id=session_id,
            user_input=str(claimed.get("input") or ""),
        )
    except HTTPException as exc:
        retryable = exc.status_code in RETRYABLE_STATUS
        await fail_intake_job(
            client,
            job_id=job_id,
            error=str(exc.detail),
            retryable=retryable,
        )
        logger.warning(
            "chat_job_failed",
            extra={
                "job_id": str(job_id),
                "status_code": exc.status_code,
                "retryable": retryable,
            },
        )
        return retryable

    await complete_intake_job(
        client,
        job_id=job_id,
        # mode="json" so nested models and any UUID/datetime land as jsonb-safe values.
        result_payload=response.model_dump(mode="json"),
    )
    logger.info("chat_job_succeeded", extra={"job_id": str(job_id)})
    return False


async def process_batch(event: dict[str, Any]) -> dict[str, Any]:
    """Process a batch, reporting partial failures.

    Partial batch responses stop one poison message from redriving its whole batch. On a
    FIFO queue they carry an extra obligation: once a message in a group is going back on
    the queue, **every later message in that group must go back too**. Delete them
    instead and a turn that arrived later would apply while the earlier one is still
    being retried — the out-of-order merge that §14.1's whole FIFO argument exists to
    prevent. Groups are independent, so a stalled conversation never blocks another.
    """
    records: list[dict[str, Any]] = list(event.get("Records") or [])
    client = await get_client()

    failures: list[dict[str, str]] = []
    blocked_groups: set[str] = set()

    for record in records:
        message_id = str(record.get("messageId") or "")
        group = group_of(record)

        if group and group in blocked_groups:
            logger.info(
                "chat_job_deferred_behind_retry",
                extra={"message_id": message_id, "group": group},
            )
            failures.append({"itemIdentifier": message_id})
            continue

        if await process_record(client, record):
            failures.append({"itemIdentifier": message_id})
            if group:
                blocked_groups.add(group)

    return {"batchItemFailures": failures}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return asyncio.run(process_batch(event))
