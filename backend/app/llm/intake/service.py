"""Intake-level orchestration helpers backed by the configured LLM provider."""

from __future__ import annotations

from typing import Any

from app.llm.providers import huggingface_provider


async def parse_user_input(
    *,
    user_input: str,
    current_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Parse free-form user intake input into structured criteria and next-step hints."""
    return await huggingface_provider.parse_user_input(
        user_input=user_input,
        current_criteria=current_criteria,
        questions=questions,
    )


async def generate_opening_question(
    *,
    welcome_message: str,
    question_key: str,
    question_type: str,
    question_options: Any | None = None,
) -> str:
    """Generate the opening intake question text via the configured provider."""
    return await huggingface_provider.generate_opening_question_text(
        welcome_message=welcome_message,
        question_key=question_key,
        question_type=question_type,
        question_options=question_options,
    )
