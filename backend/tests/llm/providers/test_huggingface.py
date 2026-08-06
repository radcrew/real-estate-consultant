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

    async def test_success_returns_parsed_json(self):
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )
        completion.choices = [
            MagicMock(message=MagicMock(content='{"text":"hello"}', refusal=None))
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=completion)
        result = await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.5,
            max_tokens=100,
        )
        assert result.text == "hello"
        kwargs = provider.client.chat.completions.create.await_args.kwargs
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["messages"][0]["role"] == "system"
        assert "JSON Schema" in kwargs["messages"][0]["content"]

    async def test_schema_instruction_can_be_suppressed(self):
        # Intake's system prompt already carries the schema; a second copy is ~1k
        # characters of duplicate prompt on every turn.
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        completion.choices = [
            MagicMock(message=MagicMock(content='{"text":"hello"}', refusal=None))
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=completion)
        await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.5,
            max_tokens=100,
            include_schema_instruction=False,
        )
        kwargs = provider.client.chat.completions.create.await_args.kwargs
        assert kwargs["messages"] == _MESSAGES

    async def test_retries_without_json_object_when_unsupported(self):
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = None
        completion.choices = [
            MagicMock(message=MagicMock(content='{"text":"ok"}', refusal=None))
        ]
        unsupported = OpenAIError("json_object unsupported")
        unsupported.status_code = 422
        provider.client.chat.completions.create = AsyncMock(
            side_effect=[unsupported, completion]
        )
        result = await provider.generate_structured_output(
            messages=_MESSAGES,
            response_format=_Schema,
            temperature=0.5,
            max_tokens=100,
        )
        assert result.text == "ok"
        assert provider.client.chat.completions.create.await_count == 2
        second_kwargs = provider.client.chat.completions.create.await_args_list[1].kwargs
        assert "response_format" not in second_kwargs

    async def test_non_json_mode_errors_do_not_retry(self):
        provider = _make_provider()
        boom = OpenAIError("upstream down")
        boom.status_code = 500
        provider.client.chat.completions.create = AsyncMock(side_effect=boom)
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502
        assert provider.client.chat.completions.create.await_count == 1

    async def test_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=httpx.Request("POST", "https://api.example.com"))
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 504

    async def test_openai_error_raises_502(self):
        provider = _make_provider()
        provider.client.chat.completions.create = AsyncMock(
            side_effect=OpenAIError("upstream down")
        )
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502

    async def test_refusal_raises_502(self):
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = None
        completion.choices = [
            MagicMock(message=MagicMock(content=None, refusal="I cannot help with that."))
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=completion)
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502

    async def test_incomplete_reply_raises_502(self):
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = None
        completion.choices = [MagicMock(message=MagicMock(content="  ", refusal=None))]
        provider.client.chat.completions.create = AsyncMock(return_value=completion)
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502

    async def test_invalid_json_raises_502(self):
        provider = _make_provider()
        completion = MagicMock()
        completion.usage = None
        completion.choices = [
            MagicMock(message=MagicMock(content="not-json", refusal=None))
        ]
        provider.client.chat.completions.create = AsyncMock(return_value=completion)
        with pytest.raises(HTTPException) as info:
            await provider.generate_structured_output(
                messages=_MESSAGES, response_format=_Schema, temperature=0.5, max_tokens=100
            )
        assert info.value.status_code == 502


class TestHuggingFaceEmbed:
    async def test_empty_texts_returns_empty_without_call(self):
        provider = _make_provider()
        with patch("app.llm.providers.huggingface.httpx.AsyncClient") as client_cls:
            result = await provider.embed(texts=[])
            assert result == []
            client_cls.assert_not_called()

    async def test_no_api_key_raises_503(self):
        provider = _make_provider(hf_token="   ")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["hello"])
        assert info.value.status_code == 503

    async def test_feature_extraction_url_strips_v1(self):
        provider = _make_provider()
        assert provider._feature_extraction_url() == (
            "https://router.huggingface.co/hf-inference/models/"
            "sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
        )

    async def test_success_returns_batch_vectors(self):
        provider = _make_provider()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.llm.providers.huggingface.httpx.AsyncClient", return_value=mock_client):
            result = await provider.embed(texts=["a", "b"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_client.post.assert_awaited_once()
        args, kwargs = mock_client.post.await_args
        assert args[0].endswith("/pipeline/feature-extraction")
        assert kwargs["json"] == {"inputs": ["a", "b"]}

    async def test_http_error_raises_502(self):
        provider = _make_provider()
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("boom"))

        with patch("app.llm.providers.huggingface.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(HTTPException) as info:
                await provider.embed(texts=["hello"])
        assert info.value.status_code == 502
