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
from app.llm.providers.routing import AUTO_ROUTE, TASK_ROUTE_SETTINGS, LlmTask


class _Schema(BaseModel):
    text: str


def _config(
    *,
    openrouter_api_key: str = "",
    hf_token: str = "",
    aws_region: str = "",
) -> MagicMock:
    # Every field must be set explicitly: a bare MagicMock attribute is truthy, so an
    # unset credential would look configured and an unset route would look pinned.
    mock = MagicMock()
    mock.openrouter_api_key = openrouter_api_key
    mock.hf_token = hf_token
    mock.aws_region = aws_region
    mock.llm_route_default = AUTO_ROUTE
    for setting in TASK_ROUTE_SETTINGS.values():
        setattr(mock, setting, AUTO_ROUTE)
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
            "app.llm.providers.routing.resolve_chat_provider_for_task",
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
        mock_resolve.assert_called_once_with(task=None, config=config)
        assert result.text == "ok"

    async def test_forwards_task_to_the_router(self):
        parsed = _Schema(text="ok")
        config = _config(openrouter_api_key="or-key")
        with patch(
            "app.llm.providers.routing.resolve_chat_provider_for_task",
            return_value=MagicMock(
                generate_structured_output=AsyncMock(return_value=parsed),
            ),
        ) as mock_resolve:
            await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=50,
                config=config,
                task=LlmTask.INTAKE_PARSE,
            )
        mock_resolve.assert_called_once_with(task=LlmTask.INTAKE_PARSE, config=config)

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


class TestIntakeEndpointOverride:
    """A pinned endpoint must reach exactly one call site and change nothing else."""

    async def test_override_routes_to_the_openai_compatible_provider(self):
        # Even with OpenRouter configured as the default: its path uses
        # beta.chat.completions.parse, which assumes that vendor's structured outputs.
        config = _config(openrouter_api_key="or-key", hf_token="hf-key")
        with patch.object(
            huggingface_provider, "generate_structured_output", new_callable=AsyncMock
        ) as hf_call, patch.object(
            openrouter_provider, "generate_structured_output", new_callable=AsyncMock
        ) as or_call:
            await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
                config=config,
                model="qwen-intake",
                base_url="http://box:8080/v1",
                api_key="box-key",
            )
        or_call.assert_not_awaited()
        kwargs = hf_call.await_args.kwargs
        assert kwargs["base_url"] == "http://box:8080/v1"
        assert kwargs["api_key"] == "box-key"
        assert kwargs["model"] == "qwen-intake"

    async def test_default_path_is_unchanged_when_overrides_are_empty(self):
        config = _config(openrouter_api_key="or-key")
        with patch.object(
            openrouter_provider, "generate_structured_output", new_callable=AsyncMock
        ) as or_call:
            await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
                config=config,
            )
        kwargs = or_call.await_args.kwargs
        assert kwargs["model"] is None
        assert kwargs["base_url"] is None
        assert kwargs["api_key"] is None

    async def test_blank_base_url_does_not_count_as_an_override(self):
        config = _config(openrouter_api_key="or-key")
        with patch.object(
            openrouter_provider, "generate_structured_output", new_callable=AsyncMock
        ) as or_call:
            await generate_structured_output(
                messages=[{"role": "user", "content": "hi"}],
                response_format=_Schema,
                temperature=0.1,
                max_tokens=100,
                config=config,
                base_url="   ",
            )
        or_call.assert_awaited_once()


class TestPinnedEndpointFallback:
    """When the self-hosted box is down, intake degrades to the router."""

    _ARGS = dict(
        messages=[{"role": "user", "content": "hi"}],
        response_format=_Schema,
        temperature=0.1,
        max_tokens=100,
        model="qwen-intake",
        base_url="http://box:8080/v1",
        api_key="box-key",
    )

    @pytest.mark.parametrize("status", [502, 503, 504])
    async def test_transport_faults_fall_back_to_the_router(self, status):
        config = _config(hf_token="hf-key")
        with patch.object(
            huggingface_provider, "generate_structured_output", new_callable=AsyncMock
        ) as call:
            call.side_effect = [
                HTTPException(status_code=status, detail="box down"),
                _Schema(text="from the router"),
            ]
            result = await generate_structured_output(config=config, **self._ARGS)
        assert result.text == "from the router"
        assert call.await_count == 2
        # The retry must not reuse the dead endpoint.
        assert call.await_args_list[1].kwargs.get("base_url") is None

    @pytest.mark.parametrize("status", [400, 401, 403, 422])
    async def test_request_and_auth_faults_stay_loud(self, status):
        # A wrong key or a malformed request would fail the same way on the router,
        # so silently retrying just doubles the cost and hides a config error.
        config = _config(hf_token="hf-key")
        with patch.object(
            huggingface_provider, "generate_structured_output", new_callable=AsyncMock
        ) as call:
            call.side_effect = HTTPException(status_code=status, detail="nope")
            with pytest.raises(HTTPException) as info:
                await generate_structured_output(config=config, **self._ARGS)
        assert info.value.status_code == status
        assert call.await_count == 1

    async def test_unpinned_calls_never_retry(self):
        config = _config(hf_token="hf-key")
        with patch.object(
            huggingface_provider, "generate_structured_output", new_callable=AsyncMock
        ) as call:
            call.side_effect = HTTPException(status_code=503, detail="down")
            with pytest.raises(HTTPException):
                await generate_structured_output(
                    messages=[{"role": "user", "content": "hi"}],
                    response_format=_Schema,
                    temperature=0.1,
                    max_tokens=100,
                    config=config,
                )
        assert call.await_count == 1

    async def test_fallback_failure_surfaces_rather_than_looping(self):
        config = _config(hf_token="hf-key")
        with patch.object(
            huggingface_provider, "generate_structured_output", new_callable=AsyncMock
        ) as call:
            call.side_effect = HTTPException(status_code=503, detail="down")
            with pytest.raises(HTTPException):
                await generate_structured_output(config=config, **self._ARGS)
        assert call.await_count == 2
