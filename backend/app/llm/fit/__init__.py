"""Fit-explanation LLM helpers."""

from app.llm.fit.prompts import (
    FIT_EXPLANATION_SYSTEM_PROMPT,
    build_fit_user_message,
    format_criteria_block_for_fit,
    format_listing_block_for_fit,
    format_score_block_for_fit,
    score_to_tier,
)
from app.llm.fit.schema import FitExplanationLLM
from app.llm.fit.service import generate_fit_explanation

__all__ = [
    "FIT_EXPLANATION_SYSTEM_PROMPT",
    "FitExplanationLLM",
    "build_fit_user_message",
    "format_criteria_block_for_fit",
    "format_listing_block_for_fit",
    "format_score_block_for_fit",
    "generate_fit_explanation",
    "score_to_tier",
]
