"""Tests for dropping filler answers the model writes when the message says nothing."""

import pytest

from app.domain.intake_criteria import drop_placeholder_values


class TestPlaceholderStrings:
    @pytest.mark.parametrize(
        "filler",
        ["Unknown", "unknown", "  UNKNOWN  ", "N/A", "n/a", "none", "null", "TBD",
         "not specified", "Not Provided", "any", "no preference", "-", "?", ""],
    )
    def test_dropped(self, filler):
        assert drop_placeholder_values({"location": filler}) == {}

    @pytest.mark.parametrize(
        "real",
        ["Austin, Texas", "Unknown Street", "Nome", "Anytown", "North Anywhere",
         "Nanaimo", "Naples"],
    )
    def test_real_values_containing_a_filler_word_survive(self, real):
        """Matching is exact, never substring — "Nome" is not "none"."""
        assert drop_placeholder_values({"location": real}) == {"location": real}


class TestLists:
    def test_drops_filler_entries(self):
        assert drop_placeholder_values({"property_type": ["Warehouse", "Unknown"]}) == {
            "property_type": ["Warehouse"]
        }

    def test_drops_the_key_when_every_entry_is_filler(self):
        assert drop_placeholder_values({"property_type": ["Unknown", "N/A"]}) == {}

    def test_drops_an_empty_list(self):
        assert drop_placeholder_values({"property_type": []}) == {}


class TestRanges:
    def test_keeps_a_range_with_a_bound(self):
        value = {"price": {"max": 2000000}}
        assert drop_placeholder_values(value) == value

    def test_drops_an_all_null_range(self):
        """The shape the schema description used to invite before it was removed."""
        assert drop_placeholder_values({"price": {"min": None, "max": None}}) == {}

    def test_drops_an_empty_range(self):
        assert drop_placeholder_values({"price": {}}) == {}

    def test_zero_is_a_real_bound(self):
        value = {"price": {"min": 0}}
        assert drop_placeholder_values(value) == value


class TestOtherTypes:
    def test_keeps_numbers_including_zero(self):
        assert drop_placeholder_values({"loading_docks": 0}) == {"loading_docks": 0}

    def test_keeps_booleans(self):
        assert drop_placeholder_values({"flag": False}) == {"flag": False}

    def test_empty_extraction(self):
        assert drop_placeholder_values({}) == {}

    def test_does_not_mutate_its_input(self):
        original = {"location": "Unknown", "size_sqft": {"min": 100}}
        drop_placeholder_values(original)
        assert original == {"location": "Unknown", "size_sqft": {"min": 100}}
