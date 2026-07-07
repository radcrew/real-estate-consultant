from app.llm.fit.prompts import (
    build_fit_user_message,
    format_criteria_block_for_fit,
    format_listing_block_for_fit,
    format_score_block_for_fit,
    score_to_tier,
)


class TestScoreToTier:
    def test_not_specified_regardless_of_value(self):
        assert score_to_tier(1.0, specified=False) == "not specified"
        assert score_to_tier(0.0, specified=False) == "not specified"

    def test_excellent_at_high_value(self):
        assert score_to_tier(0.9, specified=True) == "excellent match"

    def test_good_match_mid_high(self):
        assert score_to_tier(0.65, specified=True) == "good match"

    def test_partial_match_mid(self):
        assert score_to_tier(0.4, specified=True) == "partial match"

    def test_weak_match_low_nonzero(self):
        assert score_to_tier(0.1, specified=True) == "weak match"

    def test_no_match_at_zero(self):
        assert score_to_tier(0.0, specified=True) == "no match"

    def test_boundary_values(self):
        assert score_to_tier(0.85, specified=True) == "excellent match"
        assert score_to_tier(0.6, specified=True) == "good match"
        assert score_to_tier(0.3, specified=True) == "partial match"


class TestFormatCriteriaBlock:
    def test_known_keys_included(self):
        criteria = {"location": "Austin, TX", "price": {"min": 100, "max": 200}}
        result = format_criteria_block_for_fit(criteria)
        assert "location: Austin, TX" in result
        assert "price:" in result

    def test_empty_criteria_returns_fallback(self):
        assert format_criteria_block_for_fit({}) == "(No search criteria set yet.)"

    def test_unknown_keys_ignored(self):
        result = format_criteria_block_for_fit({"location": "Austin", "extra": "x"})
        assert "extra" not in result


class TestFormatListingBlock:
    def test_known_keys_included(self):
        row = {"address": "100 Main St", "price": 500_000}
        result = format_listing_block_for_fit(row)
        assert "address: 100 Main St" in result
        assert "price: 500000" in result

    def test_none_and_empty_values_skipped(self):
        row = {"address": None, "city": "", "price": 500_000}
        result = format_listing_block_for_fit(row)
        assert "address" not in result
        assert "city" not in result

    def test_empty_row_returns_fallback(self):
        assert format_listing_block_for_fit({}) == "(No listing details provided.)"


class TestFormatScoreBlock:
    def test_marks_unspecified_criteria(self):
        result = format_score_block_for_fit(
            {}, location_score=1.0, price_score=1.0, size_score=1.0,
        )
        assert "location: not specified" in result
        assert "price: not specified" in result
        assert "size: not specified" in result

    def test_marks_specified_criteria_by_tier(self):
        criteria = {
            "location": "Austin",
            "price": {"min": 100, "max": 200},
            "size_sqft": {"min": 1000, "max": 2000},
        }
        result = format_score_block_for_fit(
            criteria, location_score=1.0, price_score=0.5, size_score=0.1,
        )
        assert "location: excellent match" in result
        assert "price: partial match" in result
        assert "size: weak match" in result


class TestBuildFitUserMessage:
    def test_contains_all_sections(self):
        result = build_fit_user_message(
            criteria={"location": "Austin"},
            property_row={"address": "1 Main St"},
            location_score=1.0,
            price_score=1.0,
            size_score=1.0,
        )
        assert "Search criteria:" in result
        assert "Listing:" in result
        assert "Match tiers:" in result
        assert "1 Main St" in result
