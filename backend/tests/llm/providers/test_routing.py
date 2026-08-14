"""Tests for per-call-site provider routing."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.llm.providers.bedrock_chat import bedrock_chat_provider
from app.llm.providers.bedrock_embeddings import bedrock_embeddings_provider
from app.llm.providers.bedrock_qwen_chat import bedrock_qwen_chat_provider
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider
from app.llm.providers.routing import (
    AUTO_ROUTE,
    TASK_ROUTE_SETTINGS,
    LlmTask,
    resolve_chat_provider_for_task,
    resolve_embeddings_provider_for_route,
    resolve_route_name,
)


def _config(
    *,
    openrouter_api_key: str = "",
    hf_token: str = "",
    aws_region: str = "",
    default: str = AUTO_ROUTE,
    embeddings: str = AUTO_ROUTE,
    **routes: str,
) -> MagicMock:
    mock = MagicMock()
    mock.openrouter_api_key = openrouter_api_key
    mock.hf_token = hf_token
    mock.aws_region = aws_region
    mock.llm_route_default = default
    mock.llm_route_embeddings = embeddings
    for task, setting in TASK_ROUTE_SETTINGS.items():
        setattr(mock, setting, routes.get(task.value, AUTO_ROUTE))
    return mock


class TestResolveRouteName:
    def test_task_pin_wins(self):
        config = _config(intake_parse="bedrock", default="openrouter")
        assert resolve_route_name(task=LlmTask.INTAKE_PARSE, config=config) == "bedrock"

    def test_falls_through_to_default(self):
        config = _config(default="huggingface")
        assert resolve_route_name(task=LlmTask.FIT_EXPLANATION, config=config) == "huggingface"

    def test_none_task_uses_default(self):
        config = _config(default="bedrock")
        assert resolve_route_name(task=None, config=config) == "bedrock"

    def test_auto_when_nothing_pinned(self):
        config = _config()
        assert resolve_route_name(task=LlmTask.OUTREACH_DRAFT, config=config) == AUTO_ROUTE

    def test_normalises_case_and_whitespace(self):
        config = _config(intake_parse="  BedRock ")
        assert resolve_route_name(task=LlmTask.INTAKE_PARSE, config=config) == "bedrock"

    def test_blank_pin_is_treated_as_auto(self):
        config = _config(intake_parse="")
        assert resolve_route_name(task=LlmTask.INTAKE_PARSE, config=config) == AUTO_ROUTE


class TestResolveChatProviderForTask:
    @pytest.mark.parametrize(
        ("pin", "expected"),
        [
            ("openrouter", openrouter_provider),
            ("huggingface", huggingface_provider),
            ("bedrock", bedrock_chat_provider),
            ("bedrock_qwen", bedrock_qwen_chat_provider),
        ],
    )
    def test_each_pin_selects_its_provider(self, pin, expected):
        config = _config(intake_parse=pin)
        assert resolve_chat_provider_for_task(task=LlmTask.INTAKE_PARSE, config=config) is expected

    def test_bedrock_and_bedrock_qwen_are_distinct_providers(self):
        """Different SDKs: the Anthropic client cannot call a Qwen model."""
        config = _config(outreach_draft="bedrock_qwen", fit_explanation="bedrock")
        assert (
            resolve_chat_provider_for_task(task=LlmTask.OUTREACH_DRAFT, config=config)
            is bedrock_qwen_chat_provider
        )
        assert (
            resolve_chat_provider_for_task(task=LlmTask.FIT_EXPLANATION, config=config)
            is bedrock_chat_provider
        )

    def test_auto_never_selects_bedrock_qwen(self):
        """Key presence cannot tell the two Bedrock providers apart, so a pin is required."""
        config = _config(aws_region="us-east-1")
        assert (
            resolve_chat_provider_for_task(task=LlmTask.OUTREACH_DRAFT, config=config)
            is bedrock_chat_provider
        )

    def test_tasks_route_independently(self):
        """The whole point: one call site on a fine-tune, another on a general model."""
        config = _config(
            openrouter_api_key="or-key",
            intake_parse="bedrock",
            outreach_draft="openrouter",
        )
        assert (
            resolve_chat_provider_for_task(task=LlmTask.INTAKE_PARSE, config=config)
            is bedrock_chat_provider
        )
        assert (
            resolve_chat_provider_for_task(task=LlmTask.OUTREACH_DRAFT, config=config)
            is openrouter_provider
        )

    def test_auto_defers_to_key_presence(self):
        config = _config(openrouter_api_key="or-key")
        assert (
            resolve_chat_provider_for_task(task=LlmTask.INTAKE_PARSE, config=config)
            is openrouter_provider
        )

    def test_auto_without_credentials_raises_503(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            resolve_chat_provider_for_task(task=LlmTask.INTAKE_PARSE, config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "AI unavailable"

    def test_unknown_pin_raises_rather_than_falling_back(self):
        """A typo must fail loudly, not silently serve traffic from another provider."""
        config = _config(openrouter_api_key="or-key", intake_parse="grok")
        with pytest.raises(HTTPException) as info:
            resolve_chat_provider_for_task(task=LlmTask.INTAKE_PARSE, config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "The AI provider route is misconfigured."

    def test_no_task_uses_default_pin(self):
        config = _config(default="bedrock")
        assert resolve_chat_provider_for_task(config=config) is bedrock_chat_provider


class TestResolveEmbeddingsProviderForRoute:
    def test_pin_selects_bedrock_over_configured_hf(self):
        """An explicit pin is the only way to reach Bedrock while HF_TOKEN is set."""
        config = _config(hf_token="hf-key", embeddings="bedrock")
        assert resolve_embeddings_provider_for_route(config=config) is bedrock_embeddings_provider

    def test_auto_defers_to_key_presence(self):
        config = _config(hf_token="hf-key")
        assert resolve_embeddings_provider_for_route(config=config) is huggingface_provider

    def test_auto_without_credentials_raises_503(self):
        config = _config()
        with pytest.raises(HTTPException) as info:
            resolve_embeddings_provider_for_route(config=config)
        assert info.value.status_code == 503
        assert info.value.detail == "Embeddings unavailable"

    def test_unknown_pin_raises(self):
        config = _config(hf_token="hf-key", embeddings="nope")
        with pytest.raises(HTTPException) as info:
            resolve_embeddings_provider_for_route(config=config)
        assert info.value.status_code == 503


class TestRoutingTableCoverage:
    def test_every_task_has_a_setting(self):
        """A new LlmTask without a setting would silently fall through to the default."""
        assert set(TASK_ROUTE_SETTINGS) == set(LlmTask)

    def test_every_setting_exists_on_settings(self):
        from app.core.config import Settings

        for setting in [*TASK_ROUTE_SETTINGS.values(), "llm_route_default", "llm_route_embeddings"]:
            assert setting in Settings.model_fields

    def test_settings_default_to_auto(self):
        """Routing must be opt-in: defaults keep today's key-presence behaviour."""
        from app.core.config import Settings

        for setting in [*TASK_ROUTE_SETTINGS.values(), "llm_route_default", "llm_route_embeddings"]:
            assert Settings.model_fields[setting].default == AUTO_ROUTE
