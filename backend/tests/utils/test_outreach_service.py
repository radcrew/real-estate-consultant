"""Tests for generate_broker_outreach_draft."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.llm.outreach.schema import OutreachDraftEmailLLM
from app.llm.outreach.service import generate_broker_outreach_draft

_PROPERTY = {
    "address": "100 Main St",
    "city": "Austin",
    "state": "TX",
    "listing_broker_name": "Bob",
    "listing_broker_email": "bob@example.com",
}


class TestGenerateBrokerOutreachDraft:
    async def test_returns_draft_text(self):
        parsed = OutreachDraftEmailLLM(draft_email="Dear Bob,\n\nI am writing to inquire about your property at 100 Main St.")
        with patch(
            "app.llm.outreach.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ):
            result = await generate_broker_outreach_draft(property_row=_PROPERTY)
        assert result == parsed.draft_email.strip()

    async def test_empty_draft_raises_502(self):
        parsed = OutreachDraftEmailLLM.__new__(OutreachDraftEmailLLM)
        object.__setattr__(parsed, "draft_email", "   ")
        with patch(
            "app.llm.outreach.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ):
            with pytest.raises(HTTPException) as info:
                await generate_broker_outreach_draft(property_row=_PROPERTY)
        assert info.value.status_code == 502

    async def test_profile_and_auth_email_forwarded(self):
        parsed = OutreachDraftEmailLLM(draft_email="Dear Bob,\n\nI saw your listing and wanted to reach out.")
        profile = {"first_name": "Alice", "email": "alice@example.com"}
        with patch(
            "app.llm.outreach.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ) as mock_gen:
            await generate_broker_outreach_draft(
                property_row=_PROPERTY,
                profile_row=profile,
                auth_email="alice@example.com",
            )
        call_kwargs = mock_gen.call_args.kwargs
        user_msg = call_kwargs["messages"][1]["content"]
        assert "Alice" in user_msg
