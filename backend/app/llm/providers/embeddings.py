"""Embeddings entry point: resolve Hugging Face vs OpenRouter by env keys.

Priority differs from chat: HF_TOKEN wins when both keys are set so chat can
stay on OpenRouter while embeddings use HF-native models.
"""

from __future__ import annotations

from typing import Literal

from app.core.config import Settings
from app.core.config import settings as app_settings
from app.llm.providers.base import EmbeddingsProvider
from app.llm.providers.bedrock_embeddings import bedrock_embeddings_provider
from app.llm.providers.exceptions import raise_embeddings_unavailable
from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider

EmbeddingsProviderName = Literal["huggingface", "openrouter", "bedrock"]


def resolve_embeddings_provider_name(*, config: Settings) -> EmbeddingsProviderName | None:
    """Return the configured embeddings provider name, or None when no keys are set.

    Bedrock is checked last for the same reason as chat: configuring a region must not
    silently move a working workload onto a metered provider.
    """
    if config.hf_token.strip():
        return "huggingface"
    if config.openrouter_api_key.strip():
        return "openrouter"
    if config.aws_region.strip():
        return "bedrock"
    return None


def resolve_embeddings_provider(*, config: Settings | None = None) -> EmbeddingsProvider:
    """Return the active embeddings provider; raises 503 when no keys are configured."""
    active_config = config or app_settings
    provider_name = resolve_embeddings_provider_name(config=active_config)
    if provider_name == "huggingface":
        return huggingface_provider
    if provider_name == "openrouter":
        return openrouter_provider
    if provider_name == "bedrock":
        return bedrock_embeddings_provider
    raise_embeddings_unavailable()


async def embed(
    *,
    texts: list[str],
    config: Settings | None = None,
) -> list[list[float]]:
    """Embed texts via the configured provider (Hugging Face preferred when both keys set)."""
    provider = resolve_embeddings_provider(config=config)
    return await provider.embed(texts=texts)
