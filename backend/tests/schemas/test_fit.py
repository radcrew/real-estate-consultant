import uuid

import pytest
from pydantic import ValidationError

from app.schemas.fit import FitExplanationResponse, FitScoreBreakdown


class TestFitScoreBreakdown:
    def test_valid_bounds(self):
        obj = FitScoreBreakdown(location=1.0, price=0.5, size=0.0, total=75.0)
        assert obj.total == 75.0

    def test_location_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            FitScoreBreakdown(location=1.5, price=0.5, size=0.0, total=50.0)

    def test_total_out_of_bounds_raises(self):
        with pytest.raises(ValidationError):
            FitScoreBreakdown(location=1.0, price=1.0, size=1.0, total=101.0)


class TestFitExplanationResponse:
    def test_defaults_empty_lists(self):
        obj = FitExplanationResponse(
            property_id=uuid.uuid4(),
            score=FitScoreBreakdown(location=1.0, price=1.0, size=1.0, total=100.0),
            summary="Great fit.",
        )
        assert obj.strengths == []
        assert obj.considerations == []

    def test_full_fields(self):
        pid = uuid.uuid4()
        obj = FitExplanationResponse(
            property_id=pid,
            score=FitScoreBreakdown(location=1.0, price=0.5, size=0.2, total=60.0),
            summary="Decent fit.",
            strengths=["Good location"],
            considerations=["Smaller than requested"],
        )
        assert obj.property_id == pid
        assert obj.strengths == ["Good location"]
        assert obj.considerations == ["Smaller than requested"]

    def test_missing_property_id_raises(self):
        with pytest.raises(ValidationError):
            FitExplanationResponse(
                score=FitScoreBreakdown(location=1.0, price=1.0, size=1.0, total=100.0),
                summary="Great fit.",
            )
