"""Fit-explanation orchestration: LLM provider calls for match-score narratives."""

from __future__ import annotations

from typing import Any

from app.llm.fit.exceptions import raise_fit_explanation_empty
from app.llm.fit.prompts import FIT_EXPLANATION_SYSTEM_PROMPT, build_fit_user_message
from app.llm.fit.schema import FitExplanationLLM
from app.llm.providers import huggingface_provider
from app.utils.criteria_search import parse_location_fields, parse_range

_NO_CRITERIA_SUMMARY = (
    "No specific search criteria are set yet, so every listing scores neutrally. "
    "Add a location, price range, or size range to see how this listing actually "
    "compares."
)


def _has_any_criteria(criteria: dict[str, Any]) -> bool:
    if any(parse_location_fields(criteria)):
        return True
    if any(bound is not None for bound in parse_range(criteria.get("price"))):
        return True
    if any(bound is not None for bound in parse_range(criteria.get("size_sqft"))):
        return True
    return False


async def generate_fit_explanation(
    *,
    criteria: dict[str, Any],
    property_row: dict[str, Any],
    location_score: float,
    price_score: float,
    size_score: float,
) -> FitExplanationLLM:
    """Return a short narrative explaining a property's match score (not persisted).

    Skips the LLM call entirely when no criteria are set: every component is
    neutral by construction (see ``match_score_expr``), so there's nothing real
    to explain yet.
    """
    if not _has_any_criteria(criteria):
        return FitExplanationLLM(summary=_NO_CRITERIA_SUMMARY, strengths=[], considerations=[])

    user_content = build_fit_user_message(
        criteria=criteria,
        property_row=property_row,
        location_score=location_score,
        price_score=price_score,
        size_score=size_score,
    )
    messages = [
        {"role": "system", "content": FIT_EXPLANATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    parsed = await huggingface_provider.generate_structured_output(
        messages=messages,
        response_format=FitExplanationLLM,
        temperature=0.2,
        max_tokens=400,
    )
    if not parsed.summary.strip():
        raise_fit_explanation_empty()
    return parsed
