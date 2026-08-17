"""Tests for folding a turn's answers into what the session already knows."""

from app.domain.intake_criteria import merge_criteria


class TestRangesMergeBoundWise:
    def test_the_other_bound_is_added_not_substituted(self):
        """"under $1M" then "more than 100K" must keep both, not end up with only the min."""
        assert merge_criteria(
            {"price": {"max": 1000000}}, {"price": {"min": 100000}}
        ) == {"price": {"min": 100000, "max": 1000000}}

    def test_a_correction_still_overwrites_that_bound(self):
        assert merge_criteria(
            {"price": {"max": 1000000}}, {"price": {"max": 3000000}}
        ) == {"price": {"max": 3000000}}

    def test_a_correction_leaves_the_other_bound_intact(self):
        assert merge_criteria(
            {"price": {"min": 100000, "max": 1000000}}, {"price": {"max": 3000000}}
        ) == {"price": {"min": 100000, "max": 3000000}}

    def test_restating_both_bounds_replaces_both(self):
        assert merge_criteria(
            {"price": {"min": 100000, "max": 1000000}},
            {"price": {"min": 500000, "max": 2000000}},
        ) == {"price": {"min": 500000, "max": 2000000}}

    def test_a_unit_carries_forward(self):
        assert merge_criteria(
            {"size_sqft": {"max": 8000, "unit": "sqft"}}, {"size_sqft": {"min": 2000}}
        ) == {"size_sqft": {"min": 2000, "max": 8000, "unit": "sqft"}}

    def test_ranges_on_different_fields_do_not_interact(self):
        assert merge_criteria(
            {"price": {"max": 1000000}}, {"size_sqft": {"min": 5000}}
        ) == {"price": {"max": 1000000}, "size_sqft": {"min": 5000}}


class TestContradictoryBoundsDropTheStaleOne:
    def test_a_floor_above_the_stored_ceiling_drops_the_ceiling(self):
        """"more than 100" after "up to 32" stored min 100 / max 32, which matches nothing."""
        assert merge_criteria(
            {"size_sqft": {"max": 32}}, {"size_sqft": {"min": 100}}
        ) == {"size_sqft": {"min": 100}}

    def test_a_ceiling_below_the_stored_floor_drops_the_floor(self):
        assert merge_criteria(
            {"price": {"min": 1000000}}, {"price": {"max": 500000}}
        ) == {"price": {"max": 500000}}

    def test_a_floor_equal_to_the_stored_ceiling_drops_the_ceiling(self):
        """"no, more than 32" cannot mean "exactly 32", which is what keeping both gives."""
        assert merge_criteria(
            {"size_sqft": {"max": 32}}, {"size_sqft": {"min": 32}}
        ) == {"size_sqft": {"min": 32}}

    def test_a_ceiling_equal_to_the_stored_floor_drops_the_floor(self):
        assert merge_criteria(
            {"price": {"min": 500000}}, {"price": {"max": 500000}}
        ) == {"price": {"max": 500000}}

    def test_an_exact_size_stated_in_one_turn_keeps_both_bounds(self):
        """The equality rule must not block the way a bare number is stored."""
        assert merge_criteria(
            {}, {"size_sqft": {"min": 32, "max": 32}}
        ) == {"size_sqft": {"min": 32, "max": 32}}

    def test_widening_off_an_exact_size_drops_the_ceiling(self):
        assert merge_criteria(
            {"size_sqft": {"min": 32, "max": 32}}, {"size_sqft": {"min": 32}}
        ) == {"size_sqft": {"min": 32}}

    def test_the_unit_survives_a_dropped_bound(self):
        assert merge_criteria(
            {"size_sqft": {"max": 32, "unit": "sqft"}}, {"size_sqft": {"min": 100}}
        ) == {"size_sqft": {"min": 100, "unit": "sqft"}}

    def test_a_turn_restating_both_bounds_inverted_is_left_alone(self):
        """Nothing was carried forward, so there is no stale bound to identify."""
        assert merge_criteria(
            {"price": {"max": 500000}}, {"price": {"min": 900000, "max": 100000}}
        ) == {"price": {"min": 900000, "max": 100000}}

    def test_a_non_numeric_bound_does_not_raise(self):
        assert merge_criteria(
            {"size_sqft": {"max": "thirty two"}}, {"size_sqft": {"min": 100}}
        ) == {"size_sqft": {"max": "thirty two", "min": 100}}

    def test_a_null_bound_does_not_raise(self):
        assert merge_criteria(
            {"size_sqft": {"max": None}}, {"size_sqft": {"min": 100}}
        ) == {"size_sqft": {"max": None, "min": 100}}

    def test_floats_and_ints_compare(self):
        assert merge_criteria(
            {"price": {"max": 32.0}}, {"price": {"min": 100}}
        ) == {"price": {"min": 100}}

    def test_the_reported_session_ends_with_a_usable_range(self):
        """32 -> "no, more than 32" -> "more than 32sqft" -> "more than 100sqft"."""
        criteria: dict = {}
        for extracted in (
            {"size_sqft": {"max": 32}},
            {"size_sqft": {"min": 32}},
            {"size_sqft": {"min": 32}},
            {"size_sqft": {"min": 100}},
        ):
            criteria = merge_criteria(criteria, extracted)
        assert criteria == {"size_sqft": {"min": 100}}


class TestEverythingElseReplaces:
    def test_a_corrected_location_replaces(self):
        assert merge_criteria(
            {"location": "Austin, TX"}, {"location": "Houston, TX"}
        ) == {"location": "Houston, TX"}

    def test_a_corrected_property_type_replaces_rather_than_unions(self):
        """"actually, retail" means retail, not industrial-and-retail."""
        assert merge_criteria(
            {"property_type": ["industrial"]}, {"property_type": ["retail"]}
        ) == {"property_type": ["retail"]}

    def test_a_dict_that_is_not_a_range_replaces(self):
        assert merge_criteria(
            {"thing": {"a": 1}}, {"thing": {"b": 2}}
        ) == {"thing": {"b": 2}}

    def test_a_range_replacing_a_non_range_replaces(self):
        assert merge_criteria({"price": "cheap"}, {"price": {"max": 5}}) == {"price": {"max": 5}}


class TestCarryForward:
    def test_untouched_keys_survive(self):
        assert merge_criteria(
            {"location": "Austin, TX", "price": {"max": 1000000}}, {"size_sqft": {"min": 5000}}
        ) == {"location": "Austin, TX", "price": {"max": 1000000}, "size_sqft": {"min": 5000}}

    def test_the_reserved_skipped_key_carries_forward(self):
        assert merge_criteria(
            {"_skipped_fields": ["price"]}, {"location": "Austin, TX"}
        ) == {"_skipped_fields": ["price"], "location": "Austin, TX"}

    def test_empty_extraction_changes_nothing(self):
        current = {"price": {"max": 1000000}}
        assert merge_criteria(current, {}) == current

    def test_empty_current_returns_the_extraction(self):
        assert merge_criteria({}, {"price": {"max": 5}}) == {"price": {"max": 5}}

    def test_does_not_mutate_either_input(self):
        current = {"price": {"max": 1000000}}
        extracted = {"price": {"min": 100000}}
        merge_criteria(current, extracted)
        assert current == {"price": {"max": 1000000}}
        assert extracted == {"price": {"min": 100000}}
