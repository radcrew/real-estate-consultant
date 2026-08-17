"""Tests for BedrockChatProvider.generate_structured_output."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from anthropic import (
    APIStatusError,
    APITimeoutError,
    PermissionDeniedError,
    RateLimitError,
)
from fastapi import HTTPException
from pydantic import BaseModel

from app.llm.providers.bedrock_chat import BedrockChatProvider, split_system_prompt


class _Schema(BaseModel):
    text: str


def _make_provider(aws_region: str = "us-east-1") -> BedrockChatProvider:
    mock_settings = MagicMock()
    mock_settings.aws_region = aws_region
    mock_settings.bedrock_chat_model = "anthropic.claude-sonnet-5"
    mock_settings.bedrock_effort = "low"
    mock_settings.bedrock_disable_thinking = True
    mock_settings.bedrock_input_cost_per_1m = 3.0
    mock_settings.bedrock_output_cost_per_1m = 15.0
    return BedrockChatProvider(settings=mock_settings, client=AsyncMock())


def _make_completion(parsed=None, stop_reason="end_turn"):
    usage = MagicMock()
    usage.input_tokens = 10
    usage.output_tokens = 20
    usage.cache_read_input_tokens = 5
    completion = MagicMock()
    completion.parsed_output = parsed
    completion.stop_reason = stop_reason
    completion.usage = usage
    return completion


def _http_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=httpx.Request("POST", "https://bedrock.example"),
    )


_MESSAGES = [
    {"role": "system", "content": "You extract criteria."},
    {"role": "user", "content": "Hello"},
]


class TestSplitSystemPrompt:
    def test_extracts_system_turn(self):
        system, turns = split_system_prompt(_MESSAGES)
        assert system == "You extract criteria."
        assert turns == [{"role": "user", "content": "Hello"}]

    def test_no_system_turn_yields_empty_prompt(self):
        system, turns = split_system_prompt([{"role": "user", "content": "Hi"}])
        assert system == ""
        assert turns == [{"role": "user", "content": "Hi"}]

    def test_joins_multiple_system_turns(self):
        system, _ = split_system_prompt(
            [
                {"role": "system", "content": "One."},
                {"role": "system", "content": "Two."},
                {"role": "user", "content": "Hi"},
            ]
        )
        assert system == "One.\n\nTwo."


class TestBedrockChatProvider:
    async def test_no_region_raises_503(self):
        provider = _make_provider(aws_region="   ")
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 503

    async def test_success_returns_parsed_output(self):
        provider = _make_provider()
        parsed = _Schema(text="hello")
        provider.client.messages.parse = AsyncMock(return_value=_make_completion(parsed=parsed))
        result = await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.1,
            max_tokens=100,
        )
        assert result is parsed

    async def test_system_message_moves_to_top_level_parameter(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(parsed=_Schema(text="ok"))
        )
        await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.1,
            max_tokens=100,
        )
        kwargs = provider.client.messages.parse.await_args.kwargs
        assert kwargs["system"] == "You extract criteria."
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]

    async def test_temperature_is_never_forwarded(self):
        """Claude 4.7+ rejects temperature outright; forwarding it would 400 every call."""
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(parsed=_Schema(text="ok"))
        )
        await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.35,
            max_tokens=100,
        )
        kwargs = provider.client.messages.parse.await_args.kwargs
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs
        assert "top_k" not in kwargs

    async def test_thinking_disabled_by_setting(self):
        """max_tokens is sized for models without thinking, so it stays off by default."""
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(parsed=_Schema(text="ok"))
        )
        await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.1,
            max_tokens=800,
        )
        kwargs = provider.client.messages.parse.await_args.kwargs
        assert kwargs["thinking"] == {"type": "disabled"}
        assert kwargs["output_config"] == {"effort": "low"}
        assert kwargs["max_tokens"] == 800

    async def test_thinking_adaptive_when_enabled(self):
        provider = _make_provider()
        provider.settings.bedrock_disable_thinking = False
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(parsed=_Schema(text="ok"))
        )
        await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.1,
            max_tokens=4000,
        )
        kwargs = provider.client.messages.parse.await_args.kwargs
        assert kwargs["thinking"] == {"type": "adaptive"}

    async def test_refusal_raises_502(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(stop_reason="refusal")
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 502

    async def test_max_tokens_stop_reason_raises_502(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            return_value=_make_completion(parsed=_Schema(text="cut"), stop_reason="max_tokens")
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=10,
            )
        assert info.value.status_code == 502

    async def test_missing_parsed_output_raises_502(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(return_value=_make_completion(parsed=None))
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 502

    async def test_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            side_effect=APITimeoutError(request=httpx.Request("POST", "https://bedrock.example"))
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 504

    async def test_rate_limit_raises_503(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            side_effect=RateLimitError("slow down", response=_http_response(429), body=None)
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 503

    async def test_permission_denied_raises_503(self):
        """Model access not enabled for this account/region in the Bedrock console."""
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            side_effect=PermissionDeniedError(
                "access denied", response=_http_response(403), body=None
            )
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 503

    async def test_other_api_error_raises_502(self):
        provider = _make_provider()
        provider.client.messages.parse = AsyncMock(
            side_effect=APIStatusError("boom", response=_http_response(500), body=None)
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
            )
        assert info.value.status_code == 502
