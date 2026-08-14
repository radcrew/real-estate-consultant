"""Per-call-site provider routing.

The resolvers in ``chat.py`` and ``embeddings.py`` pick one provider for the whole
process from which credentials happen to be set. That is too coarse once different call
sites want different models — a narrow fine-tune for criteria extraction, a general
model for prose, a metered provider for embeddings.

Routing is opt-in: every setting defaults to ``"auto"``, which defers to the existing
key-presence order, so adding this module changes no behaviour until a route is pinned.
"""

from __future__ import annotations

import logging
from enum import StrEnum

from app.core.config import Settings
from app.core.config import settings as app_settings
from app.llm.providers.base import ChatProvider, EmbeddingsProvider
from app.llm.providers.bedrock_chat import bedrock_chat_provider
from app.llm.providers.bedrock_embeddings import bedrock_embeddings_provider
from app.llm.providers.bedrock_qwen_chat import bedrock_qwen_chat_provider
from app.llm.providers.chat import resolve_chat_provider
from app.llm.providers.embeddings import (
    resolve_embeddings_provider,
    resolve_embeddings_provider_name,
)
from app.llm.providers.exceptions import raise_embeddings_unavailable
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider
from app.utils.exceptions import raise_service_unavailable

AUTO_ROUTE = "auto"

logger = logging.getLogger(__name__)


class LlmTask(StrEnum):
    """A chat call site. Each one routes independently."""

    INTAKE_PARSE = "intake_parse"
    OPENING_QUESTION = "opening_question"
    FIT_EXPLANATION = "fit_explanation"
    OUTREACH_DRAFT = "outreach_draft"


CHAT_PROVIDERS: dict[str, ChatProvider] = {
    "openrouter": openrouter_provider,
    "huggingface": huggingface_provider,
    "bedrock": bedrock_chat_provider,
    # Pin-only: key presence cannot distinguish "bedrock" from "bedrock_qwen", so an
    # explicit route is the only way to reach the Converse-API provider.
    "bedrock_qwen": bedrock_qwen_chat_provider,
}

EMBEDDINGS_PROVIDERS: dict[str, EmbeddingsProvider] = {
    "huggingface": huggingface_provider,
    "openrouter": openrouter_provider,
    "bedrock": bedrock_embeddings_provider,
}

# Which Settings field names the model for each provider, for embedding provenance.
EMBEDDING_MODEL_SETTINGS: dict[str, str] = {
    "bedrock": "bedrock_embedding_model",
    "huggingface": "hf_embedding_model",
    "openrouter": "openrouter_embedding_model",
}

TASK_ROUTE_SETTINGS: dict[LlmTask, str] = {
    LlmTask.INTAKE_PARSE: "llm_route_intake_parse",
    LlmTask.OPENING_QUESTION: "llm_route_opening_question",
    LlmTask.FIT_EXPLANATION: "llm_route_fit_explanation",
    LlmTask.OUTREACH_DRAFT: "llm_route_outreach_draft",
}


def resolve_route_name(*, task: LlmTask | None, config: Settings) -> str:
    """Return the pinned provider name for ``task``, or ``"auto"``.

    A task with no pin of its own falls through to ``llm_route_default``.
    """
    if task is not None:
        setting = TASK_ROUTE_SETTINGS[task]
        name = str(getattr(config, setting, AUTO_ROUTE) or AUTO_ROUTE).strip().lower()
        if name and name != AUTO_ROUTE:
            return name
    return str(config.llm_route_default or AUTO_ROUTE).strip().lower() or AUTO_ROUTE


def _pinned(
    providers: dict[str, ChatProvider] | dict[str, EmbeddingsProvider],
    name: str,
    *,
    setting: str,
):
    """Look up a pinned provider, refusing rather than silently ignoring a typo."""
    try:
        return providers[name]
    except KeyError:
        logger.error(
            "llm_route_unknown",
            extra={"setting": setting, "value": name, "known": sorted(providers)},
        )
        raise_service_unavailable("The AI provider route is misconfigured.")


def resolve_chat_provider_for_task(
    *,
    task: LlmTask | None = None,
    config: Settings | None = None,
) -> ChatProvider:
    """Return the chat provider for ``task``, honouring its pin or falling back to auto."""
    active_config = config or app_settings
    name = resolve_route_name(task=task, config=active_config)
    if name == AUTO_ROUTE:
        return resolve_chat_provider(config=active_config)
    setting = TASK_ROUTE_SETTINGS[task] if task is not None else "llm_route_default"
    return _pinned(CHAT_PROVIDERS, name, setting=setting)


def resolve_embeddings_route_name(*, config: Settings) -> str:
    """Return the pinned embeddings provider name, or ``"auto"``."""
    return str(config.llm_route_embeddings or AUTO_ROUTE).strip().lower() or AUTO_ROUTE


def resolve_embeddings_provider_for_route(
    *,
    config: Settings | None = None,
) -> EmbeddingsProvider:
    """Return the embeddings provider, honouring ``llm_route_embeddings`` or auto."""
    active_config = config or app_settings
    name = resolve_embeddings_route_name(config=active_config)
    if name == AUTO_ROUTE:
        return resolve_embeddings_provider(config=active_config)
    return _pinned(EMBEDDINGS_PROVIDERS, name, setting="llm_route_embeddings")


def resolve_embeddings_model_id(*, config: Settings | None = None) -> str:
    """Return ``provider:model`` for the active embeddings route.

    Stored beside each vector so rows produced by a superseded model stay findable —
    embeddings are only comparable against others from the same model.
    """
    active_config = config or app_settings
    name = resolve_embeddings_route_name(config=active_config)
    if name == AUTO_ROUTE:
        name = resolve_embeddings_provider_name(config=active_config) or ""
    if name not in EMBEDDING_MODEL_SETTINGS:
        raise_embeddings_unavailable()
    return f"{name}:{getattr(active_config, EMBEDDING_MODEL_SETTINGS[name])}"
