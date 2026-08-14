"""Tests for QwenLambdaProvider.generate_structured_output."""
from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, ConnectTimeoutError, ParamValidationError
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.llm.providers.qwen_lambda import QwenLambdaProvider, is_transient


class _Schema(BaseModel):
    text: str = Field(min_length=1)


def _make_provider(
    *,
    aws_region: str = "us-east-1",
    function_name: str = "qwen-inference-prod",
    client: object | None = None,
):
    mock_settings = MagicMock()
    mock_settings.aws_region = aws_region
    mock_settings.qwen_inference_function_name = function_name
    mock_settings.qwen_model_version = "qwen-ft-2026-01"
    return QwenLambdaProvider(
        settings=mock_settings,
        client=MagicMock() if client is None else client,
    )


def _payload(body: dict) -> dict:
    return {"Payload": io.BytesIO(json.dumps(body).encode())}


def _reply(text: str = '{"text": "hello"}', **extra) -> dict:
    return _payload({"text": text, **extra})


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Invoke")


_MESSAGES = [
    {"role": "system", "content": "You extract criteria."},
    {"role": "user", "content": "3 bed in Austin under 500k"},
]


async def _generate(provider, *, temperature: float = 0.1, max_tokens: int = 800):
    return await provider.generate_structured_output(
        messages=_MESSAGES,
        response_format=_Schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )


class TestIsTransient:
    @pytest.mark.parametrize(
        "code", ["TooManyRequestsException", "ThrottlingException", "ServiceException"]
    )
    def test_transient_codes(self, code):
        assert is_transient(_client_error(code))

    @pytest.mark.parametrize(
        "code",
        ["AccessDeniedException", "ResourceNotFoundException", "InvalidRequestContentException"],
    )
    def test_deterministic_codes_are_not_retried(self, code):
        """Retrying these buys the same failure twice."""
        assert not is_transient(_client_error(code))

    def test_transport_timeouts_are_transient(self):
        assert is_transient(ConnectTimeoutError(endpoint_url="https://lambda"))

    def test_other_botocore_errors_are_not(self):
        assert not is_transient(ParamValidationError(report="bad params"))


class TestQwenLambdaProvider:
    async def test_no_region_raises_503(self):
        provider = _make_provider(aws_region="   ")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_no_function_name_raises_503(self):
        provider = _make_provider(function_name="  ")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_unconfigured_does_not_build_a_client(self):
        """boto3 raises on a blank region, so the guard must come first."""
        provider = _make_provider(aws_region="", client=None)
        provider._client = None
        with pytest.raises(HTTPException):
            await _generate(provider)
        assert provider._client is None

    async def test_success_returns_validated_output(self):
        provider = _make_provider()
        provider.client.invoke.return_value = _reply()
        result = await _generate(provider)
        assert isinstance(result, _Schema)
        assert result.text == "hello"

    async def test_sends_messages_schema_name_and_limits(self):
        provider = _make_provider()
        provider.client.invoke.return_value = _reply()
        await _generate(provider, temperature=0.1, max_tokens=800)
        kwargs = provider.client.invoke.call_args.kwargs
        assert kwargs["FunctionName"] == "qwen-inference-prod"
        assert kwargs["InvocationType"] == "RequestResponse"
        sent = json.loads(kwargs["Payload"])
        assert sent["schema_name"] == "_Schema"
        assert sent["max_tokens"] == 800
        # The system turn stays in place: the GGUF chat template renders roles itself.
        assert sent["messages"] == _MESSAGES

    async def test_temperature_forwarded(self):
        """Qwen honours temperature, unlike the Anthropic path which must drop it."""
        provider = _make_provider()
        provider.client.invoke.return_value = _reply()
        await _generate(provider, temperature=0.1)
        assert json.loads(provider.client.invoke.call_args.kwargs["Payload"])["temperature"] == 0.1

    async def test_function_error_raises_502_without_parsing_the_body(self):
        """Lambda returns 200 when the handler raised; only FunctionError says otherwise."""
        provider = _make_provider()
        provider.client.invoke.return_value = {
            "FunctionError": "Unhandled",
            "Payload": io.BytesIO(b'{"errorMessage": "OOM"}'),
        }
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_unreadable_payload_raises_502(self):
        provider = _make_provider()
        provider.client.invoke.return_value = {"Payload": io.BytesIO(b"not json")}
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_missing_text_raises_502(self):
        provider = _make_provider()
        provider.client.invoke.return_value = _payload({"usage": {"prompt_tokens": 5}})
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_length_stop_reason_raises_502(self):
        """The grammar guarantees shape, not that the model finished saying it."""
        provider = _make_provider()
        provider.client.invoke.return_value = _reply(stop_reason="length")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_schema_violating_text_raises_502(self):
        provider = _make_provider()
        provider.client.invoke.return_value = _reply(text='{"text": ""}')
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_retries_once_on_throttling_then_succeeds(self):
        provider = _make_provider()
        provider.client.invoke.side_effect = [
            _client_error("TooManyRequestsException"),
            _reply(),
        ]
        result = await _generate(provider)
        assert result.text == "hello"
        assert provider.client.invoke.call_count == 2

    async def test_retry_is_not_chained(self):
        """One attempt, no chaining — a second failure degrades instead of looping."""
        provider = _make_provider()
        provider.client.invoke.side_effect = _client_error("TooManyRequestsException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert provider.client.invoke.call_count == 2
        assert info.value.status_code == 503

    async def test_content_failure_is_never_retried(self):
        """Retrying a schema violation buys the same bad answer twice."""
        provider = _make_provider()
        provider.client.invoke.return_value = _reply(text='{"text": ""}')
        with pytest.raises(HTTPException):
            await _generate(provider)
        assert provider.client.invoke.call_count == 1

    async def test_access_denied_is_not_retried_and_raises_503(self):
        provider = _make_provider()
        provider.client.invoke.side_effect = _client_error("AccessDeniedException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert provider.client.invoke.call_count == 1
        assert info.value.status_code == 503

    async def test_missing_function_raises_503(self):
        provider = _make_provider()
        provider.client.invoke.side_effect = _client_error("ResourceNotFoundException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_transport_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.invoke.side_effect = ConnectTimeoutError(endpoint_url="https://lambda")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 504

    async def test_other_client_error_raises_502(self):
        provider = _make_provider()
        provider.client.invoke.side_effect = _client_error("InvalidRequestContentException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502
