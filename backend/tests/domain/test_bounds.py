"""Tests for comparator-based bound-direction correction.

Every wording here is one the intake model was measured on in
``ml/eval/results/0.5b-lora-v2-q4km-r3.json``, or a near neighbour of one, so a change
that breaks these is a change that breaks a case we know occurs.
"""

import pytest

from app.domain.bounds import bound_sides_in, correct_bound_direction


class TestBoundSidesIn:
    @pytest.mark.parametrize(
        "text",
        ["up to $2M", "no more than $2M", "under $2M", "less than $2M",
         "lower than $2M", "below $2M", "at most $2M", "not over $2M",
         "$2M or less", "just shy of 8,000 sqft", "we'd cap it at $1.5M",
         "maximum $2M"],
    )
    def test_upper_bounds(self, text):
        assert bound_sides_in(text) == {"max"}

    @pytest.mark.parametrize(
        "text",
        ["at least $500K", "more than $500K", "higher than $500K", "greater than $500K",
         "over $500K", "above $500K", "starting at $500K", "upwards of $750K",
         "north of $500K", "$400k and up", "$500K or more", "minimum $500K"],
    )
    def test_lower_bounds(self, text):
        assert bound_sides_in(text) == {"min"}

    @pytest.mark.parametrize(
        "text,expected",
        [("no less than $500K", {"min"}),
         ("no lower than $500K", {"min"}),
         ("nothing below 5,000 sqft", {"min"}),
         ("nothing under 5,000 sqft", {"min"}),
         ("no more than $2M", {"max"}),
         ("no higher than $2M", {"max"}),
         ("nothing over $2M", {"max"}),
         ("nothing above $2M", {"max"})],
    )
    def test_negation_beats_the_comparator_inside_it(self, text, expected):
        """'no less than' is a floor, not a ceiling — the longer form must win."""
        assert bound_sides_in(text) == expected

    @pytest.mark.parametrize(
        "text",
        ["between $500K and $2M", "half a million", "$500K floor, $2M ceiling",
         "warehouse in Austin", ""],
    )
    def test_no_comparator(self, text):
        assert bound_sides_in(text) == set()

    def test_both_directions(self):
        assert bound_sides_in("its cost is lower than $2M, its cost is higher than $500K") == {
            "min",
            "max",
        }

    def test_floor_is_not_a_comparator(self):
        """'ground floor' is a building feature here, not a lower bound."""
        assert bound_sides_in("ground floor retail under $2M") == {"max"}


class TestCorrectBoundDirection:
    def test_flips_a_max_the_model_put_in_min(self):
        assert correct_bound_direction(
            {"price": {"min": 2000000}}, "cost should be lower than $2M"
        ) == {"price": {"max": 2000000}}

    def test_flips_a_min_the_model_put_in_max(self):
        assert correct_bound_direction(
            {"size_sqft": {"max": 8000}}, "nothing below 8,000 sqft"
        ) == {"size_sqft": {"min": 8000}}

    def test_leaves_a_correct_value_alone(self):
        value = {"price": {"max": 2000000}}
        assert correct_bound_direction(value, "my budget range is less than $2M") == value

    def test_leaves_a_two_sided_value_alone(self):
        value = {"price": {"min": 500000, "max": 2000000}}
        assert correct_bound_direction(value, "under $2M") == value

    def test_leaves_an_ambiguous_message_alone(self):
        """Both directions stated: the model's answer beats a coin flip."""
        value = {"price": {"min": 2000000}}
        assert correct_bound_direction(
            value, "its cost is lower than $2M, its cost is higher than $500K"
        ) == value

    def test_leaves_a_message_with_no_comparator_alone(self):
        value = {"price": {"max": 500000}}
        assert correct_bound_direction(value, "half a million") == value

    def test_ignores_non_range_fields(self):
        value = {"location": "Austin, Texas", "property_type": ["Warehouse"]}
        assert correct_bound_direction(value, "warehouse in Austin under $2M") == value

    def test_corrects_only_the_range_field_in_a_mixed_payload(self):
        assert correct_bound_direction(
            {"location": "Austin, Texas", "price": {"min": 2000000}},
            "Austin, lower than $2M",
        ) == {"location": "Austin, Texas", "price": {"max": 2000000}}

    def test_handles_several_range_fields_at_once(self):
        assert correct_bound_direction(
            {"price": {"max": 2000000}, "size_sqft": {"max": 8000}},
            "at least $2M and at least 8,000 sqft",
        ) == {"price": {"min": 2000000}, "size_sqft": {"min": 8000}}

    def test_treats_a_null_bound_as_absent(self):
        """The schema types min/max as numbers, so a null is not a stated bound."""
        assert correct_bound_direction(
            {"price": {"min": 2000000, "max": None}}, "lower than $2M"
        ) == {"price": {"max": 2000000}}

    def test_does_not_mutate_its_input(self):
        original = {"price": {"min": 2000000}}
        correct_bound_direction(original, "lower than $2M")
        assert original == {"price": {"min": 2000000}}

    def test_empty_extraction(self):
        assert correct_bound_direction({}, "lower than $2M") == {}
