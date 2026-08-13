"""Tests for chat provider resolution and facade."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from app.llm.providers.bedrock_chat import bedrock_chat_provider
from app.llm.providers.chat import (
    generate_structured_output,
    resolve_chat_provider,
    resolve_chat_provider_name,
)
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider


class _Schema(BaseModel):
    text: str


def _config(
    *,
    openrouter_api_key: str = "",
    hf_token: str = "",
    aws_region: str = "",
) -> MagicMock:
    # Every credential must be set explicitly: a bare MagicMock attribute is truthy,
    # so an unset field would look configured and quietly select the wrong provider.
    mock = MagicMock()
    mock.openrouter_api_key = openrouter_api_key
    mock.hf_token = hf_token
    mock.aws_region = aws_region
    return mock


class TestResolveChatProviderName:
    def test_openrouter_wins_when_both_keys_set(self):
        config = _config(openrouter_api_key="or-key", hf_token="hf-key")
        assert resolve_chat_provider_name(config=config) == "openrouter"

    def test_huggingface_when_only_hf_token(self):
        config = _config(hf_token="hf-key")
        assert resolve_chat_provider_name(config=config) == "huggingface"

    def test_openrouter_when_only_openrouter_key(self):
        config = _config(openrouter_api_key="or-key")
        assert resolve_chat_provider_name(config=config) == "openrouter"

    def test_bedrock_when_only_aws_region(self):
        config = _config(aws_region="us-east-1")
        assert resolve_chat_provider_name(config=config) == "bedrock"

    def test_bedrock_does_not_displace_openrouter(self):
        """Bedrock bills per token, so a configured region must not silently take over."""
        config = _config(openrouter_api_key="or-key", aws_region="us-east-1")
        assert resolve_chat_provider_name(config=config) == "openrouter"

    def test_bedrock_does_not_displace_huggingface(self):
        config = _config(hf_token="hf-key", aws_region="us-east-1")
        assert resolve_chat_provider_name(config=config) == "huggingface"

    def test_none_when_no_keys(self):
        config = _config()
        assert resolve_chat_provider_name(config=config) is None


class TestResolveChatProvider:
    def test_returns_openrouter_provider(self):
        config = _config(openrouter_api_key="or-key")
        assert resolve_chat_provider(config=config) is openrouter_provider

    def test_returns_huggingface_provider(self):
        config = _config(hf_token="hf-key")
        assert resolve_chat_provider(config=config) is huggingface_provider

    def test_returns_bedrock_provider(self):
        config = _config(aws_region="us-east-1")
        assert resolve_chat_provider(config=config) is bedrock_chat_provider

    def test_raises_ai_unavailable_when_no_keys(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            resolve_chat_provider(config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "AI unavailable"


class TestGenerateStructuredOutput:
    async def test_delegates_to_resolved_provider(self):
        parsed = _Schema(text="ok")
        config = _config(openrouter_api_key="or-key")
        with patch(
            "app.llm.providers.chat.resolve_chat_provider",
            return_value=MagicMock(
                generate_structured_output=AsyncMock(return_value=parsed),
            ),
        ) as mock_resolve:
            result = await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=50,
                config=config,
            )
        mock_resolve.assert_called_once_with(config=config)
        assert result.text == "ok"

    async def test_raises_ai_unavailable_without_keys(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=50,
                config=config,
            )
        assert info.value.status_code == 503
        assert info.value.detail == "AI unavailable"
