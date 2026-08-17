"""Admission control for the LLM-backed intake endpoints.

These routes are authenticated and the session is owned by its creator, so this is not
about anonymous abuse — it is about how much one account can spend per minute. Both LLM
intake routes cost money per request: creating an LLM-mode session runs the
opening-question model, and every turn runs the extraction model.

Metering matters more here than on most endpoints because of what queueing changes. Today
an abused endpoint costs a burst of provider calls. Once turns are queued (§14.1) each
accepted request becomes a durable job the worker will faithfully pay for, so the backlog
keeps spending long after the flood stops. Admission control is what keeps the queue a
buffer rather than an amplifier.

The address window is the wider net and the session window paces one conversation. This
is a ceiling, not a bill: per-tenant budgets (§19) are the second layer, and now that
every session has an owner there is an identity to attribute spend to.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, Query, Request

from app.core.config import settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.utils.exceptions import raise_too_many_requests

WINDOW_SECONDS = 60.0
RETRY_AFTER_HEADER = {"Retry-After": "60"}


def client_ip(request: Request) -> str:
    """Best-effort client address.

    Behind a proxy the socket peer is the proxy, so the left-most ``X-Forwarded-For``
    entry is the client. That header is caller-supplied and therefore only trustworthy
    because the platform overwrites it — expose this API without a trusted proxy in front
    and the per-address limit becomes advisory, since an attacker can vary the header per
    request. The per-session limit does not have that weakness.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded.strip():
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


class IntakeAdmissionControl:
    """Two sliding windows: one per address, one per session."""

    def __init__(self, *, ip_per_minute: int, session_per_minute: int) -> None:
        self._ip_limiter = SlidingWindowRateLimiter(
            max_calls=ip_per_minute,
            window_seconds=WINDOW_SECONDS,
        )
        self._session_limiter = SlidingWindowRateLimiter(
            max_calls=session_per_minute,
            window_seconds=WINDOW_SECONDS,
        )

    def check_entry(self, *, address: str) -> None:
        """Budget every LLM-backed entry point against one address.

        Sessions are free to mint, so a per-session limit alone is no defence: the same
        caller can simply start another. The address budget is what bounds the total.
        """
        if not self._ip_limiter.allow(address):
            raise_too_many_requests(
                "Too many requests. Please wait a moment and try again.",
                headers=RETRY_AFTER_HEADER,
            )

    def check_turn(self, *, address: str, session_id: UUID | str) -> None:
        """A conversation turn: charged to both the address and the session."""
        self.check_entry(address=address)
        if not self._session_limiter.allow(str(session_id)):
            raise_too_many_requests(
                "You're sending messages too quickly. Please wait a moment.",
                headers=RETRY_AFTER_HEADER,
            )


intake_admission = IntakeAdmissionControl(
    ip_per_minute=settings.intake_ip_rate_limit_per_minute,
    session_per_minute=settings.intake_session_rate_limit_per_minute,
)


def admit_intake_session_creation(
    request: Request,
    mode: Annotated[Literal["llm", "guided"], Query()] = "guided",
) -> None:
    """Meter session creation, but only in ``llm`` mode.

    Guided mode returns the questionnaire's own text and calls no provider, so throttling
    it would cost usability and protect nothing.
    """
    if mode != "llm":
        return
    intake_admission.check_entry(address=client_ip(request))


def admit_intake_llm_turn(request: Request, session_id: UUID) -> None:
    intake_admission.check_turn(address=client_ip(request), session_id=session_id)


AdmitIntakeSessionCreation = Depends(admit_intake_session_creation)
AdmitIntakeLlmTurn = Depends(admit_intake_llm_turn)
