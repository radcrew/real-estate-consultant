"""Shared protocols for LLM providers."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)


class ChatProvider(Protocol):
    """OpenAI-compatible structured chat completion provider."""

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        response_format: type[StructuredOutputT],
        temperature: float,
        max_tokens: int,
        include_schema_instruction: bool = True,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> StructuredOutputT:
        """Return a typed structured completion for the given messages.

        Set ``include_schema_instruction`` False when ``messages`` already carries the
        schema, so the provider does not prepend a second copy of it.

        ``model`` / ``base_url`` / ``api_key`` pin one task to another OpenAI-compatible
        endpoint. All three unset means the provider's configured defaults.
        """
        ...


class EmbeddingsProvider(Protocol):
    """OpenAI-compatible text embeddings provider."""

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in order."""
        ...