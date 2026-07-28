"""Shared protocol for chat LLM providers."""

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
    ) -> StructuredOutputT:
        """Return a typed structured completion for the given messages."""
        ...
