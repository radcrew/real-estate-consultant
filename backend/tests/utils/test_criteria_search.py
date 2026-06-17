import pytest
from app.utils.criteria_search import (
    gaussian_target_sigma,
    ilike_pattern,
    parse_location_fields,
    parse_range,
)


class TestIlikePattern:
    def test_wraps_in_percent(self):
        assert ilike_pattern("austin") == "%austin%"

    def test_escapes_percent(self):
        assert ilike_pattern("100%") == "%100\\%%"

    def test_escapes_underscore(self):
        assert ilike_pattern("foo_bar") == "%foo\\_bar%"

    def test_escapes_backslash(self):
        assert ilike_pattern("a\\b") == "%a\\\\b%"


class TestParseRange:
    def test_both_bounds(self):
        assert parse_range({"min": 100, "max": 500}) == (100.0, 500.0)

    def test_min_only(self):
        lo, hi = parse_range({"min": 50})
        assert lo == 50.0
        assert hi is None

    def test_max_only(self):
        lo, hi = parse_range({"max": 200})
        assert lo is None
        assert hi == 200.0

    def test_non_dict_returns_none_none(self):
        assert parse_range("not-a-dict") == (None, None)
        assert parse_range(None) == (None, None)
        assert parse_range([1, 2]) == (None, None)

    def test_string_numbers_parsed(self):
        assert parse_range({"min": "10", "max": "20"}) == (10.0, 20.0)


class TestGaussianTargetSigma:
    def test_both_bounds_returns_midpoint(self):
        mid, sigma = gaussian_target_sigma(100.0, 300.0)
        assert mid == 200.0
        assert sigma == 100.0

    def test_sigma_at_least_one(self):
        _, sigma = gaussian_target_sigma(10.0, 10.0)
        assert sigma >= 1.0

    def test_lo_only(self):
        mid, sigma = gaussian_target_sigma(1000.0, None)
        assert mid == 1000.0
        assert sigma >= 1.0

    def test_hi_only(self):
        mid, sigma = gaussian_target_sigma(None, 500.0)
        assert mid == 500.0
        assert sigma >= 1.0

    def test_both_none_returns_none_sigma_one(self):
        mid, sigma = gaussian_target_sigma(None, None)
        assert mid is None
        assert sigma == 1.0


class TestParseLocationFields:
    def test_string_city_state(self):
        label, city, state, country = parse_location_fields({"location": "Austin, TX"})
        assert label == "Austin, TX"
        assert city == "Austin"
        assert state is None  # two tokens → city + country
        assert country == "TX"

    def test_string_city_state_country(self):
        label, city, state, country = parse_location_fields({"location": "Austin, TX, US"})
        assert label == "Austin, TX, US"
        assert city == "Austin"
        assert state == "TX"
        assert country == "US"

    def test_country_alias_normalised(self):
        _, _, _, country = parse_location_fields({"location": "Austin, TX, USA"})
        assert country == "US"

    def test_dict_location(self):
        label, city, state, country = parse_location_fields({
            "location": {"label": "Dallas", "city": "Dallas", "state": "TX", "country": "US"}
        })
        assert label == "Dallas"
        assert city == "Dallas"
        assert state == "TX"
        assert country == "US"

    def test_missing_location_returns_nones(self):
        assert parse_location_fields({}) == (None, None, None, None)

    def test_none_location_returns_nones(self):
        assert parse_location_fields({"location": None}) == (None, None, None, None)

    def test_empty_string_location_returns_nones(self):
        assert parse_location_fields({"location": "   "}) == (None, None, None, None)

    def test_single_token_returns_label_only(self):
        label, city, state, country = parse_location_fields({"location": "Austin"})
        assert label == "Austin"
        assert city is None
        assert state is None
        assert country is None

    def test_unknown_country_alias_returned_as_is(self):
        _, _, _, country = parse_location_fields({"location": "Austin, TX, Canada"})
        assert country == "Canada"
