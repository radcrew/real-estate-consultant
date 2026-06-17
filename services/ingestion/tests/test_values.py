"""Tests for app.utils.values — string/numeric helpers."""
import pytest
from app.utils.values import clean_str_or_none, first_valid, round_or_none


class TestCleanStrOrNone:
    def test_none_returns_none(self):
        assert clean_str_or_none(None) is None

    def test_blank_string_returns_none(self):
        assert clean_str_or_none("   ") is None

    def test_empty_string_returns_none(self):
        assert clean_str_or_none("") is None

    def test_strips_whitespace(self):
        assert clean_str_or_none("  hello  ") == "hello"

    def test_int_converted_to_str(self):
        assert clean_str_or_none(42) == "42"

    def test_float_converted_to_str(self):
        assert clean_str_or_none(3.14) == "3.14"

    def test_normal_string_returned(self):
        assert clean_str_or_none("Austin") == "Austin"


class TestFirstValid:
    def test_returns_first_non_empty(self):
        assert first_valid([None, "", "  ", "Austin"]) == "Austin"

    def test_returns_none_when_all_empty(self):
        assert first_valid([None, "", "   "]) is None

    def test_empty_list_returns_none(self):
        assert first_valid([]) is None

    def test_first_valid_wins(self):
        assert first_valid(["Dallas", "Austin"]) == "Dallas"

    def test_strips_whitespace(self):
        assert first_valid(["  TX  "]) == "TX"


class TestRoundOrNone:
    def test_none_returns_none(self):
        assert round_or_none(None) is None

    def test_rounds_to_6_places_by_default(self):
        assert round_or_none(1.123456789) == 1.123457

    def test_custom_places(self):
        assert round_or_none(1.5678, 2) == 1.57

    def test_zero_stays_zero(self):
        assert round_or_none(0.0) == 0.0

    def test_integer_value(self):
        assert round_or_none(5.0) == 5.0
