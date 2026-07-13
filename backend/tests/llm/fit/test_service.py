"""Tests for generate_fit_explanation."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.llm.fit.schema import FitExplanationLLM
from app.llm.fit.service import generate_fit_explanation

_CRITERIA = {"location": "Austin", "price": {"min": 100_000, "max": 300_000}}
_PROPERTY = {"address": "100 Main St", "city": "Austin", "price": 250_000}


class TestGenerateFitExplanation:
    async def test_returns_llm_result(self):
        parsed = FitExplanationLLM(
            summary="This listing is in Austin and close to your target price.",
            strengths=["Right city", "Price near target"],
            considerations=[],
        )
        with patch(
            "app.llm.fit.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ):
            result = await generate_fit_explanation(
                criteria=_CRITERIA,
                property_row=_PROPERTY,
                location_score=1.0,
                price_score=0.9,
                size_score=1.0,
            )
        assert result == parsed

    async def test_empty_summary_raises_502(self):
        parsed = FitExplanationLLM.__new__(FitExplanationLLM)
        object.__setattr__(parsed, "summary", "   ")
        object.__setattr__(parsed, "strengths", [])
        object.__setattr__(parsed, "considerations", [])
        with patch(
            "app.llm.fit.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ):
            with pytest.raises(HTTPException) as info:
                await generate_fit_explanation(
                    criteria=_CRITERIA,
                    property_row=_PROPERTY,
                    location_score=1.0,
                    price_score=0.9,
                    size_score=1.0,
                )
        assert info.value.status_code == 502

    async def test_no_criteria_short_circuits_without_llm_call(self):
        with patch(
            "app.llm.fit.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
        ) as mock_gen:
            result = await generate_fit_explanation(
                criteria={},
                property_row=_PROPERTY,
                location_score=1.0,
                price_score=1.0,
                size_score=1.0,
            )
        mock_gen.assert_not_called()
        assert "criteria" in result.summary.lower()

    async def test_partial_criteria_still_calls_llm(self):
        parsed = FitExplanationLLM(
            summary="This listing is right in your target city.",
            strengths=["Right city"],
            considerations=["No price range set to compare against"],
        )
        with patch(
            "app.llm.fit.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=parsed,
        ) as mock_gen:
            await generate_fit_explanation(
                criteria={"location": "Austin"},
                property_row=_PROPERTY,
                location_score=1.0,
                price_score=1.0,
                size_score=1.0,
            )
        mock_gen.assert_called_once()
