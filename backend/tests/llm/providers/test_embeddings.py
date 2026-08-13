"""Tests for embeddings provider resolution and facade."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.llm.providers.bedrock_embeddings import bedrock_embeddings_provider
from app.llm.providers.embeddings import (
    embed,
    resolve_embeddings_provider,
    resolve_embeddings_provider_name,
)
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider


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


class TestResolveEmbeddingsProviderName:
    def test_huggingface_wins_when_both_keys_set(self):
        config = _config(openrouter_api_key="or-key", hf_token="hf-key")
        assert resolve_embeddings_provider_name(config=config) == "huggingface"

    def test_huggingface_when_only_hf_token(self):
        config = _config(hf_token="hf-key")
        assert resolve_embeddings_provider_name(config=config) == "huggingface"

    def test_openrouter_when_only_openrouter_key(self):
        config = _config(openrouter_api_key="or-key")
        assert resolve_embeddings_provider_name(config=config) == "openrouter"

    def test_bedrock_when_only_aws_region(self):
        config = _config(aws_region="us-east-1")
        assert resolve_embeddings_provider_name(config=config) == "bedrock"

    def test_bedrock_does_not_displace_huggingface(self):
        """Bedrock bills per token, so a configured region must not silently take over."""
        config = _config(hf_token="hf-key", aws_region="us-east-1")
        assert resolve_embeddings_provider_name(config=config) == "huggingface"

    def test_none_when_no_keys(self):
        config = _config()
        assert resolve_embeddings_provider_name(config=config) is None


class TestResolveEmbeddingsProvider:
    def test_returns_huggingface_provider(self):
        config = _config(hf_token="hf-key")
        assert resolve_embeddings_provider(config=config) is huggingface_provider

    def test_returns_openrouter_provider(self):
        config = _config(openrouter_api_key="or-key")
        assert resolve_embeddings_provider(config=config) is openrouter_provider

    def test_returns_bedrock_provider(self):
        config = _config(aws_region="us-east-1")
        assert resolve_embeddings_provider(config=config) is bedrock_embeddings_provider

    def test_raises_embeddings_unavailable_when_no_keys(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            resolve_embeddings_provider(config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "Embeddings unavailable"


class TestEmbed:
    async def test_delegates_to_resolved_provider(self):
        vectors = [[0.1, 0.2], [0.3, 0.4]]
        config = _config(hf_token="hf-key")
        with patch(
            "app.llm.providers.embeddings.resolve_embeddings_provider",
            return_value=MagicMock(embed=AsyncMock(return_value=vectors)),
        ) as mock_resolve:
            result = await embed(texts=["a", "b"], config=config)
        mock_resolve.assert_called_once_with(config=config)
        assert result == vectors

    async def test_raises_embeddings_unavailable_without_keys(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            await embed(texts=["a"], config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "Embeddings unavailable"
