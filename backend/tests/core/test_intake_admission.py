"""Tests for admission control on the anonymous, LLM-backed intake routes."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException, Request

from app.core.intake_admission import (
    IntakeAdmissionControl,
    admit_intake_session_creation,
    client_ip,
)


def _request(*, headers: dict[str, str] | None = None, peer: str | None = "10.0.0.1") -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/intake-sessions/",
        "headers": raw,
        "client": (peer, 51234) if peer else None,
    }
    return Request(scope)


class TestClientIp:
    def test_prefers_the_leftmost_forwarded_entry(self):
        """Behind a proxy the socket peer is the proxy, not the caller."""
        request = _request(headers={"x-forwarded-for": "203.0.113.9, 70.41.3.18, 10.0.0.1"})
        assert client_ip(request) == "203.0.113.9"

    def test_falls_back_to_real_ip_header(self):
        assert client_ip(_request(headers={"x-real-ip": "198.51.100.7"})) == "198.51.100.7"

    def test_falls_back_to_the_socket_peer(self):
        assert client_ip(_request()) == "10.0.0.1"

    def test_blank_forwarded_header_does_not_become_the_key(self):
        """An empty header must not collapse every caller into one shared bucket."""
        request = _request(headers={"x-forwarded-for": "   "})
        assert client_ip(request) == "10.0.0.1"

    def test_unknown_when_there_is_no_peer(self):
        assert client_ip(_request(peer=None)) == "unknown"


class TestIntakeAdmissionControl:
    def test_entry_allows_up_to_the_address_budget(self):
        admission = IntakeAdmissionControl(ip_per_minute=2, session_per_minute=10)
        admission.check_entry(address="203.0.113.9")
        admission.check_entry(address="203.0.113.9")
        with pytest.raises(HTTPException) as info:
            admission.check_entry(address="203.0.113.9")
        assert info.value.status_code == 429

    def test_addresses_are_metered_independently(self):
        admission = IntakeAdmissionControl(ip_per_minute=1, session_per_minute=10)
        admission.check_entry(address="203.0.113.9")
        admission.check_entry(address="198.51.100.7")

    def test_turn_is_charged_to_the_session_too(self):
        admission = IntakeAdmissionControl(ip_per_minute=100, session_per_minute=2)
        session = uuid4()
        admission.check_turn(address="203.0.113.9", session_id=session)
        admission.check_turn(address="203.0.113.9", session_id=session)
        with pytest.raises(HTTPException) as info:
            admission.check_turn(address="203.0.113.9", session_id=session)
        assert info.value.status_code == 429

    def test_sessions_are_metered_independently(self):
        admission = IntakeAdmissionControl(ip_per_minute=100, session_per_minute=1)
        admission.check_turn(address="203.0.113.9", session_id=uuid4())
        admission.check_turn(address="203.0.113.9", session_id=uuid4())

    def test_address_budget_survives_new_sessions(self):
        """The point of the address budget: sessions are free to mint.

        A per-session limit alone is no defence, because the same caller just starts
        another conversation.
        """
        admission = IntakeAdmissionControl(ip_per_minute=2, session_per_minute=100)
        admission.check_turn(address="203.0.113.9", session_id=uuid4())
        admission.check_turn(address="203.0.113.9", session_id=uuid4())
        with pytest.raises(HTTPException) as info:
            admission.check_turn(address="203.0.113.9", session_id=uuid4())
        assert info.value.status_code == 429

    def test_refusal_tells_the_caller_when_to_return(self):
        admission = IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1)
        admission.check_entry(address="203.0.113.9")
        with pytest.raises(HTTPException) as info:
            admission.check_entry(address="203.0.113.9")
        assert info.value.headers == {"Retry-After": "60"}

    def test_a_rejected_turn_is_not_charged_to_the_session(self):
        """Rejected at the door means no provider call, so the session keeps its budget."""
        admission = IntakeAdmissionControl(ip_per_minute=1, session_per_minute=2)
        session = uuid4()
        admission.check_turn(address="203.0.113.9", session_id=session)
        with pytest.raises(HTTPException):
            admission.check_turn(address="203.0.113.9", session_id=session)
        # The address is exhausted, but the session spent only one of its two.
        admission.check_turn(address="198.51.100.7", session_id=session)


class TestSessionCreationAdmission:
    def test_guided_mode_is_never_throttled(self, monkeypatch):
        """Guided intake calls no provider, so metering it protects nothing."""
        admission = IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1)
        monkeypatch.setattr("app.core.intake_admission.intake_admission", admission)
        request = _request(headers={"x-forwarded-for": "203.0.113.9"})
        for _ in range(5):
            admit_intake_session_creation(request, mode="guided")

    def test_llm_mode_is_metered(self, monkeypatch):
        """Creating an llm session runs the opening-question model — it costs money."""
        admission = IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1)
        monkeypatch.setattr("app.core.intake_admission.intake_admission", admission)
        request = _request(headers={"x-forwarded-for": "203.0.113.9"})
        admit_intake_session_creation(request, mode="llm")
        with pytest.raises(HTTPException) as info:
            admit_intake_session_creation(request, mode="llm")
        assert info.value.status_code == 429
