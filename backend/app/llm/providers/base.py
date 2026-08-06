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
    ) -> StructuredOutputT:
        """Return a typed structured completion for the given messages.

        Set ``include_schema_instruction`` False when ``messages`` already carries the
        schema, so the provider does not prepend a second copy of it.
        """
        ...


class EmbeddingsProvider(Protocol):
    """OpenAI-compatible text embeddings provider."""

    async def embed(self, *, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, in order."""
        ...