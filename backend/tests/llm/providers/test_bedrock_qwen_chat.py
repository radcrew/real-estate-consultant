"""Tests for BedrockQwenChatProvider.generate_structured_output (Converse API)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.llm.providers.bedrock_qwen_chat import (
    STRUCTURED_OUTPUT_TOOL,
    BedrockQwenChatProvider,
    to_converse_messages,
)


class _Schema(BaseModel):
    """Structured reply."""

    text: str = Field(min_length=1)


def _make_provider(aws_region: str = "us-east-1", client: object | None = None):
    mock_settings = MagicMock()
    mock_settings.aws_region = aws_region
    mock_settings.bedrock_qwen_chat_model = "qwen.qwen3-32b-v1:0"
    mock_settings.bedrock_qwen_disable_thinking = True
    mock_settings.bedrock_qwen_input_cost_per_1m = 0.5
    mock_settings.bedrock_qwen_output_cost_per_1m = 1.0
    return BedrockQwenChatProvider(
        settings=mock_settings,
        client=MagicMock() if client is None else client,
    )


def _response(
    *,
    tool_input: dict | None = None,
    stop_reason: str = "tool_use",
    tool_name: str = STRUCTURED_OUTPUT_TOOL,
    content: list | None = None,
) -> dict:
    if content is None:
        content = (
            [] if tool_input is None else [{"toolUse": {"name": tool_name, "input": tool_input}}]
        )
    return {
        "output": {"message": {"role": "assistant", "content": content}},
        "stopReason": stop_reason,
        "usage": {"inputTokens": 10, "outputTokens": 20, "totalTokens": 30},
    }


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Converse")


_MESSAGES = [
    {"role": "system", "content": "You draft emails."},
    {"role": "user", "content": "Write to the broker."},
]


async def _generate(provider, *, temperature: float = 0.35, max_tokens: int = 2048):
    return await provider.generate_structured_output(
        messages=_MESSAGES,
        response_format=_Schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )


class TestToConverseMessages:
    def test_wraps_string_content_in_a_text_block(self):
        assert to_converse_messages([{"role": "user", "content": "Hi"}]) == [
            {"role": "user", "content": [{"text": "Hi"}]}
        ]

    def test_passes_existing_block_lists_through(self):
        blocks = [{"text": "already a block"}]
        assert to_converse_messages([{"role": "user", "content": blocks}]) == [
            {"role": "user", "content": blocks}
        ]


class TestBedrockQwenChatProvider:
    async def test_no_region_raises_503(self):
        provider = _make_provider(aws_region="   ")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_no_region_does_not_build_a_client(self):
        """boto3 raises on a blank region, so the guard must come before construction."""
        provider = _make_provider(aws_region="", client=None)
        provider._client = None
        with pytest.raises(HTTPException):
            await _generate(provider)
        assert provider._client is None

    async def test_success_returns_validated_tool_input(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": "hello"})
        result = await _generate(provider)
        assert isinstance(result, _Schema)
        assert result.text == "hello"

    async def test_system_message_moves_to_top_level_parameter(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": "ok"})
        await _generate(provider)
        kwargs = provider.client.converse.call_args.kwargs
        assert kwargs["system"] == [{"text": "You draft emails."}]
        assert kwargs["messages"] == [
            {"role": "user", "content": [{"text": "Write to the broker."}]}
        ]

    async def test_temperature_is_forwarded(self):
        """Unlike the Anthropic provider, which must drop it — hence per-task routing."""
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": "ok"})
        await _generate(provider, temperature=0.35, max_tokens=2048)
        kwargs = provider.client.converse.call_args.kwargs
        assert kwargs["inferenceConfig"] == {"maxTokens": 2048, "temperature": 0.35}

    async def test_forces_the_structured_output_tool(self):
        """Left to its own choice the model may answer in prose, which no schema rescues."""
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": "ok"})
        await _generate(provider)
        tool_config = provider.client.converse.call_args.kwargs["toolConfig"]
        assert tool_config["toolChoice"] == {"tool": {"name": STRUCTURED_OUTPUT_TOOL}}
        spec = tool_config["tools"][0]["toolSpec"]
        assert spec["name"] == STRUCTURED_OUTPUT_TOOL
        assert spec["inputSchema"]["json"] == _Schema.model_json_schema()

    async def test_thinking_disabled_by_setting(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": "ok"})
        await _generate(provider)
        kwargs = provider.client.converse.call_args.kwargs
        assert kwargs["additionalModelRequestFields"] == {"enable_thinking": False}

    async def test_thinking_field_omitted_when_disabled_flag_is_false(self):
        """The switch is model-revision specific; the flag is the escape hatch."""
        provider = _make_provider()
        provider.settings.bedrock_qwen_disable_thinking = False
        provider.client.converse.return_value = _response(tool_input={"text": "ok"})
        await _generate(provider)
        assert "additionalModelRequestFields" not in provider.client.converse.call_args.kwargs

    async def test_max_tokens_stop_reason_raises_502(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(
            tool_input={"text": "cut"}, stop_reason="max_tokens"
        )
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_missing_tool_call_raises_502(self):
        """A model that answered in prose produced no structured output to return."""
        provider = _make_provider()
        provider.client.converse.return_value = _response(
            content=[{"text": "Sure, here is an email."}], stop_reason="end_turn"
        )
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_tool_call_under_another_name_is_ignored(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(
            tool_input={"text": "ok"}, tool_name="something_else"
        )
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_content_filtered_raises_502(self):
        provider = _make_provider()
        provider.client.converse.return_value = _response(stop_reason="content_filtered")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    async def test_schema_violating_tool_input_raises_502(self):
        """The grammar of a tool schema is advisory; validation is what actually holds."""
        provider = _make_provider()
        provider.client.converse.return_value = _response(tool_input={"text": ""})
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502

    @pytest.mark.parametrize(
        "code", ["ThrottlingException", "TooManyRequestsException", "ServiceQuotaExceededException"]
    )
    async def test_throttling_raises_503(self, code):
        provider = _make_provider()
        provider.client.converse.side_effect = _client_error(code)
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_access_denied_raises_503(self):
        """Model access not enabled for this account/region in the Bedrock console."""
        provider = _make_provider()
        provider.client.converse.side_effect = _client_error("AccessDeniedException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 503

    async def test_model_timeout_code_raises_504(self):
        provider = _make_provider()
        provider.client.converse.side_effect = _client_error("ModelTimeoutException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 504

    async def test_read_timeout_raises_504(self):
        provider = _make_provider()
        provider.client.converse.side_effect = ReadTimeoutError(endpoint_url="https://bedrock")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 504

    async def test_other_client_error_raises_502(self):
        provider = _make_provider()
        provider.client.converse.side_effect = _client_error("ValidationException")
        with pytest.raises(HTTPException) as info:
            await _generate(provider)
        assert info.value.status_code == 502
