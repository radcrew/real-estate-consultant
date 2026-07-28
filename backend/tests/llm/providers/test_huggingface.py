"""Tests for HuggingFaceProvider.generate_structured_output."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException
from openai import APITimeoutError, OpenAIError
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.llm.providers.huggingface import HuggingFaceProvider


class _Schema(BaseModel):
    text: str


def _make_provider(hf_token: str = "tok") -> HuggingFaceProvider:
    mock_settings = MagicMock()
    mock_settings.hf_token = hf_token
    mock_settings.hf_model = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    mock_settings.hf_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    mock_settings.hf_base_url = "https://router.huggingface.co/v1"
    mock_settings.hf_input_cost_per_1m = 0.2
    mock_settings.hf_output_cost_per_1m = 0.2
    mock_client = AsyncMock()
    return HuggingFaceProvider(settings=mock_settings, client=mock_client)


def _make_completion(parsed=None, refusal=None):
    msg = MagicMock()
    msg.parsed = parsed
    msg.refusal = refusal
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    completion = MagicMock()
    completion.choices = [MagicMock(message=msg)]
    completion.usage = usage
    return completion


_MESSAGES = [{"role": "user", "content": "Hello"}]


class TestHuggingFaceProvider:
    async def test_no_api_key_raises_503(self):
        provider = _make_provider(hf_token="   ")
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES,
                response_format=_Schema,
                temperature=0.5,
                max_tokens=100,
            )
        assert info.value.status_code == 503

    async def test_success_returns_parsed(self):
        provider = _make_provider()
        parsed = _Schema(text="hello")
        provider.client.beta.chat.completions.parse = AsyncMock(
            return_value=_make_completion(parsed=parsed)
        )
        result = await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.5,
            max_tokens=100,
        )
        assert result.text == "hello"

    async def test_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.beta.chat.completions.parse = AsyncMock(
            side_effect=APITimeoutError(request=httpx.Request("POST", "https://api.example.com"))
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 504

    async def test_openai_error_raises_502(self):
        provider = _make_provider()
        provider.client.beta.chat.completions.parse = AsyncMock(
            side_effect=OpenAIError("upstream down")
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502

    async def test_refusal_raises_502(self):
        provider = _make_provider()
        provider.client.beta.chat.completions.parse = AsyncMock(
            return_value=_make_completion(parsed=None, refusal="I cannot help with that.")
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502

    async def test_incomplete_reply_raises_502(self):
        provider = _make_provider()
        provider.client.beta.chat.completions.parse = AsyncMock(
            return_value=_make_completion(parsed=None, refusal=None)
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502


class TestHuggingFaceEmbed:
    async def test_empty_texts_returns_empty_without_call(self):
        provider = _make_provider()
        provider.client.embeddings.create = AsyncMock()
        result = await provider.embed(texts=[])
        assert result == []
        provider.client.embeddings.create.assert_not_called()

    async def test_no_api_key_raises_503(self):
        provider = _make_provider(hf_token="   ")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["hello"])
        assert info.value.status_code == 503

    async def test_success_returns_ordered_vectors(self):
        provider = _make_provider()
        item0 = MagicMock(index=1, embedding=[0.3, 0.4])
        item1 = MagicMock(index=0, embedding=[0.1, 0.2])
        response = MagicMock(data=[item0, item1], usage=None)
        provider.client.embeddings.create = AsyncMock(return_value=response)
        result = await provider.embed(texts=["a", "b"])
        assert result == [[0.1, 0.2], [0.3, 0.4]]
