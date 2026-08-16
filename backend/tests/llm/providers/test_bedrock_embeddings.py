"""Tests for BedrockEmbeddingsProvider.embed."""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError
from fastapi import HTTPException

from app.llm.providers.bedrock_embeddings import BedrockEmbeddingsProvider, chunked


def _make_provider(aws_region: str = "us-east-1", batch_size: int = 96, dimensions: int = 0):
    mock_settings = MagicMock()
    mock_settings.aws_region = aws_region
    mock_settings.bedrock_embedding_model = "cohere.embed-english-v3"
    mock_settings.bedrock_embedding_batch_size = batch_size
    # A real int, not a MagicMock: the provider compares this against 0, and a mock would
    # raise TypeError rather than exercise either branch.
    mock_settings.bedrock_embedding_dimensions = dimensions
    return BedrockEmbeddingsProvider(settings=mock_settings, client=MagicMock())


def _body(payload: dict) -> dict:
    return {"body": io.BytesIO(json.dumps(payload).encode())}


def _respond_with_vectors(provider, *, dim: int = 4):
    """Return one distinct vector per input text, echoing its position."""

    def _invoke(**kwargs):
        texts = json.loads(kwargs["body"])["texts"]
        return _body({"embeddings": [[float(hash(t) % 10)] * dim for t in texts]})

    provider.client.invoke_model.side_effect = _invoke


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "InvokeModel")


class TestChunked:
    def test_splits_preserving_order(self):
        assert chunked(["a", "b", "c", "d", "e"], 2) == [["a", "b"], ["c", "d"], ["e"]]

    def test_single_chunk_when_under_size(self):
        assert chunked(["a", "b"], 96) == [["a", "b"]]

    def test_zero_size_does_not_hang(self):
        assert chunked(["a", "b"], 0) == [["a"], ["b"]]


class TestBedrockEmbeddingsProvider:
    async def test_empty_input_short_circuits(self):
        provider = _make_provider()
        assert await provider.embed(texts=[]) == []
        provider.client.invoke_model.assert_not_called()

    async def test_no_region_raises_503(self):
        provider = _make_provider(aws_region="   ")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["hello"])
        assert info.value.status_code == 503

    async def test_returns_one_vector_per_text(self):
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1, 0.2], [0.3, 0.4]]})
        vectors = await provider.embed(texts=["a", "b"])
        assert vectors == [[0.1, 0.2], [0.3, 0.4]]

    async def test_sends_cohere_request_shape(self):
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1]]})
        await provider.embed(texts=["a"])
        kwargs = provider.client.invoke_model.call_args.kwargs
        assert kwargs["modelId"] == "cohere.embed-english-v3"
        assert json.loads(kwargs["body"]) == {"texts": ["a"], "input_type": "search_document"}

    async def test_omits_output_dimension_when_unset(self):
        # v3 has one fixed width and rejects the parameter, so it must not be sent at all.
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1]]})
        await provider.embed(texts=["a"])
        assert "output_dimension" not in json.loads(
            provider.client.invoke_model.call_args.kwargs["body"],
        )

    async def test_requests_configured_width(self):
        # v4 returns 1536 unless asked, which the vector(1024) column rejects.
        provider = _make_provider(dimensions=1024)
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1] * 1024]})
        await provider.embed(texts=["a"])
        body = json.loads(provider.client.invoke_model.call_args.kwargs["body"])
        assert body["output_dimension"] == 1024

    async def test_wrong_width_raises_502(self):
        # Caught here rather than at the insert, where it surfaces as an opaque type error
        # nowhere near the setting that caused it.
        provider = _make_provider(dimensions=1024)
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1] * 1536]})
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 502
        assert "1024" in info.value.detail

    async def test_batches_and_preserves_order(self):
        """find_similar_listings zips vectors positionally, so order is load-bearing."""
        provider = _make_provider(batch_size=2)
        texts = [f"text-{index}" for index in range(5)]
        _respond_with_vectors(provider)
        vectors = await provider.embed(texts=texts)
        assert len(vectors) == 5
        assert provider.client.invoke_model.call_count == 3
        sent = [
            json.loads(call.kwargs["body"])["texts"]
            for call in provider.client.invoke_model.call_args_list
        ]
        assert sent == [["text-0", "text-1"], ["text-2", "text-3"], ["text-4"]]

    async def test_nested_float_response_shape(self):
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body(
            {"embeddings": {"float": [[0.1, 0.2]]}}
        )
        assert await provider.embed(texts=["a"]) == [[0.1, 0.2]]

    async def test_count_mismatch_raises_502(self):
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body({"embeddings": [[0.1]]})
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a", "b"])
        assert info.value.status_code == 502

    async def test_empty_response_raises_502(self):
        provider = _make_provider()
        provider.client.invoke_model.return_value = _body({"embeddings": []})
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 502

    async def test_throttling_raises_503(self):
        provider = _make_provider()
        provider.client.invoke_model.side_effect = _client_error("ThrottlingException")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 503

    async def test_access_denied_raises_503(self):
        provider = _make_provider()
        provider.client.invoke_model.side_effect = _client_error("AccessDeniedException")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 503

    async def test_model_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.invoke_model.side_effect = _client_error("ModelTimeoutException")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 504

    async def test_read_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.invoke_model.side_effect = ReadTimeoutError(endpoint_url="https://bedrock")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 504

    async def test_other_client_error_raises_502(self):
        provider = _make_provider()
        provider.client.invoke_model.side_effect = _client_error("ValidationException")
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 502


class TestLazyClient:
    def test_client_not_built_until_used(self):
        """boto3 raises on a blank region, so an eager client would break every import."""
        mock_settings = MagicMock()
        mock_settings.aws_region = ""
        provider = BedrockEmbeddingsProvider(settings=mock_settings)
        assert provider._client is None

    async def test_blank_region_raises_before_touching_boto3(self):
        mock_settings = MagicMock()
        mock_settings.aws_region = ""
        provider = BedrockEmbeddingsProvider(settings=mock_settings)
        with pytest.raises(HTTPException) as info:
            await provider.embed(texts=["a"])
        assert info.value.status_code == 503
        assert provider._client is None
