"""Tests for Bedrock Guardrails screening of intake free text."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import HTTPException

from app.clients.bedrock_guardrail import BedrockGuardrail, contains_blocked


def _make_guardrail(
    *,
    guardrail_id: str = "gr-123",
    aws_region: str = "us-east-1",
    fail_open: bool = False,
    client: object | None = None,
) -> BedrockGuardrail:
    mock_settings = MagicMock()
    mock_settings.bedrock_guardrail_id = guardrail_id
    mock_settings.bedrock_guardrail_version = "DRAFT"
    mock_settings.bedrock_guardrail_fail_open = fail_open
    mock_settings.aws_region = aws_region
    return BedrockGuardrail(
        settings=mock_settings,
        client=MagicMock() if client is None else client,
    )


def _intervened(*, masked: str | None = None, action: str = "ANONYMIZED") -> dict:
    return {
        "action": "GUARDRAIL_INTERVENED",
        "assessments": [{"sensitiveInformationPolicy": {"piiEntities": [{"action": action}]}}],
        "outputs": [{"text": masked}] if masked is not None else [],
    }


class TestContainsBlocked:
    def test_finds_a_blocked_verdict_at_any_depth(self):
        assert contains_blocked([{"topicPolicy": {"topics": [{"action": "BLOCKED"}]}}])

    def test_anonymised_is_not_blocked(self):
        """Masking is the feature working, not a refusal."""
        assert not contains_blocked(
            [{"sensitiveInformationPolicy": {"a": [{"action": "ANONYMIZED"}]}}]
        )

    def test_empty_assessments_are_not_blocked(self):
        assert not contains_blocked([])


class TestDisabled:
    async def test_no_guardrail_id_passes_text_through(self):
        """Priced per text unit, so the whole feature is opt-in."""
        guardrail = _make_guardrail(guardrail_id="")
        outcome = await guardrail.screen("my budget is 2M", source="INPUT")
        assert outcome == ("my budget is 2M", False)
        guardrail.client.apply_guardrail.assert_not_called()

    async def test_a_policy_without_a_region_refuses_rather_than_skipping(self):
        """The silent-bypass trap: requiring a region to consider screening "enabled"
        would turn a blank AWS_REGION into an off switch — the operator configures a PII
        control, nothing runs, nothing logs, and fail-open never applies because the
        failure path is never reached."""
        guardrail = _make_guardrail(aws_region="")
        assert guardrail.enabled
        with pytest.raises(HTTPException) as info:
            await guardrail.screen("my budget is 2M", source="INPUT")
        assert info.value.status_code == 503
        guardrail.client.apply_guardrail.assert_not_called()

    async def test_a_missing_region_honours_fail_open(self):
        """It is an outage-shaped condition, so the same switch governs it."""
        guardrail = _make_guardrail(aws_region="", fail_open=True)
        assert await guardrail.screen("my budget is 2M", source="INPUT") == (
            "my budget is 2M",
            False,
        )

    async def test_blank_text_is_not_sent(self):
        guardrail = _make_guardrail()
        await guardrail.screen("   ", source="INPUT")
        guardrail.client.apply_guardrail.assert_not_called()


class TestScreen:
    async def test_clean_text_is_returned_unchanged(self):
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.return_value = {"action": "NONE"}
        assert await guardrail.screen("warehouse in Austin", source="INPUT") == (
            "warehouse in Austin",
            False,
        )

    async def test_masked_text_replaces_the_original(self):
        """The point of the control: what gets stored is the redacted version."""
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.return_value = _intervened(
            masked="my address is {PII}"
        )
        outcome = await guardrail.screen("my address is 1 Main St", source="INPUT")
        assert outcome == ("my address is {PII}", False)

    async def test_a_blocked_verdict_keeps_the_original_for_the_caller_to_discard(self):
        """Storing the policy's message as though the user wrote it would be worse."""
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.return_value = {
            "action": "GUARDRAIL_INTERVENED",
            "assessments": [{"topicPolicy": {"topics": [{"action": "BLOCKED"}]}}],
            "outputs": [{"text": "Sorry, I can't help with that."}],
        }
        outcome = await guardrail.screen("something disallowed", source="INPUT")
        assert outcome.blocked is True
        assert outcome.text == "something disallowed"

    @pytest.mark.parametrize("source", ["INPUT", "OUTPUT"])
    async def test_the_source_is_forwarded(self, source):
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.return_value = {"action": "NONE"}
        await guardrail.screen("text", source=source)
        assert guardrail.client.apply_guardrail.call_args.kwargs["source"] == source

    async def test_the_configured_policy_is_used(self):
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.return_value = {"action": "NONE"}
        await guardrail.screen("text", source="INPUT")
        kwargs = guardrail.client.apply_guardrail.call_args.kwargs
        assert kwargs["guardrailIdentifier"] == "gr-123"
        assert kwargs["guardrailVersion"] == "DRAFT"
        assert kwargs["content"] == [{"text": {"text": "text"}}]


class TestOutage:
    @pytest.mark.parametrize(
        "error",
        [
            ClientError({"Error": {"Code": "ThrottlingException"}}, "ApplyGuardrail"),
            EndpointConnectionError(endpoint_url="https://bedrock"),
        ],
    )
    async def test_fails_closed_by_default(self, error):
        """A screening control that silently stops screening is worse than an error:
        the PII it exists to catch reaches storage with nothing recording the gap."""
        guardrail = _make_guardrail()
        guardrail.client.apply_guardrail.side_effect = error
        with pytest.raises(HTTPException) as info:
            await guardrail.screen("my budget is 2M", source="INPUT")
        assert info.value.status_code == 503

    async def test_fail_open_is_available_and_explicit(self):
        guardrail = _make_guardrail(fail_open=True)
        guardrail.client.apply_guardrail.side_effect = EndpointConnectionError(
            endpoint_url="https://bedrock"
        )
        assert await guardrail.screen("my budget is 2M", source="INPUT") == (
            "my budget is 2M",
            False,
        )


class TestLazyClient:
    async def test_a_disabled_guardrail_never_builds_a_client(self):
        guardrail = _make_guardrail(guardrail_id="", client=None)
        guardrail._client = None
        await guardrail.screen("text", source="INPUT")
        assert guardrail._client is None
