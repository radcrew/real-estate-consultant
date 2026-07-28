"""LLM provider integrations."""

from app.llm.providers.huggingface import huggingface_provider
from app.llm.providers.openrouter import openrouter_provider

__all__ = [
    "huggingface_provider",
    "openrouter_provider",
]
