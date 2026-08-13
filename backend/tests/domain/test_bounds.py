"""Tests for comparator-based bound-direction correction.

Every wording here is one the intake model was measured on in
``intake-model/pipeline/eval/results/0.5b-lora-v2-q4km-r3.json``, or a near neighbour of
one, so a change that breaks these is a change that breaks a case we know occurs.
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
         "north of $500K", "$400k and up", "$500K or more", "minimum $500K",
         "in excess of $500K", "beyond $500K", "exceeding $500K"],
    )
    def test_lower_bounds(self, text):
        assert bound_sides_in(text) == {"min"}

    @pytest.mark.parametrize(
        "text,expected",
        [("its size is larger than 32 sqft", {"min"}),
         ("bigger than 5,000 sqft", {"min"}),
         ("longer than 200 ft", {"min"}),
         ("wider than 60 ft", {"min"}),
         ("taller than 24 ft", {"min"}),
         ("smaller than 3,000 sqft", {"max"}),
         ("shorter than 100 ft", {"max"}),
         ("narrower than 40 ft", {"max"})],
    )
    def test_size_comparatives(self, text, expected):
        """Matched as a class: listing them one at a time is how 'larger than' leaked."""
        assert bound_sides_in(text) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [("no less than $500K", {"min"}),
         ("no lower than $500K", {"min"}),
         ("no smaller than 5,000 sqft", {"min"}),
         ("not smaller than 5,000 sqft", {"min"}),
         ("nothing below 5,000 sqft", {"min"}),
         ("nothing under 5,000 sqft", {"min"}),
         ("no more than $2M", {"max"}),
         ("no higher than $2M", {"max"}),
         ("no larger than 8,000 sqft", {"max"}),
         ("not exceeding $2M", {"max"}),
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

    def test_drops_a_bound_the_message_never_stated(self):
        """500000 appears nowhere in "under $2M", so the model invented it."""
        assert correct_bound_direction(
            {"price": {"min": 500000, "max": 2000000}}, "under $2M"
        ) == {"price": {"max": 2000000}}

    def test_keeps_both_bounds_when_the_message_states_both(self):
        value = {"price": {"min": 500000, "max": 2000000}}
        assert correct_bound_direction(value, "between $500K and $2M") == value

    def test_each_figure_takes_its_own_comparator(self):
        """A whole-message reading sees both directions here and can say nothing."""
        assert correct_bound_direction(
            {"price": {"min": 0, "max": 1000000}, "size_sqft": {"min": 100, "max": 10000}},
            "a building that costs less than $1M, size is bigger than 100sqft",
        ) == {"price": {"max": 1000000}, "size_sqft": {"min": 100}}

    def test_corrects_the_side_using_the_figures_own_comparator(self):
        """"$2M" is governed by "lower than", so the bound belongs in max."""
        assert correct_bound_direction(
            {"price": {"min": 2000000}},
            "its cost is lower than $2M, its cost is higher than $500K",
        ) == {"price": {"max": 2000000}}

    def test_an_exact_figure_with_no_comparator_keeps_both_bounds(self):
        """The convention that a plain size sets min and max to the same value."""
        value = {"size_sqft": {"min": 8000, "max": 8000}}
        assert correct_bound_direction(value, "8,000 square feet") == value

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


class TestMagnitudeCorrection:
    """The 0.5B reads a large budget and then writes it short.

    Measured on the served Q4 with the production prompt, stock and tuned alike -- v4 was
    byte-for-byte identical to the untuned model on every probe, so this is a capacity
    limit rather than anything fine-tuning did:

        up to $3M   -> 3,000,000  ok      up to $30M  ->  3,000,000   10x low
        up to $9.5M -> 9,500,000  ok      up to $150M ->  1,500,000  100x low
        up to 30k   ->    30,000  ok      $45,000,000 ->  4,500,000   10x low

    Two things hold in every miss: the significant digits are right, and the largest value
    it produced anywhere on the ladder was 9,500,000. It is losing zeros, not misreading
    the figure -- and "$30M" is 30000000 by arithmetic, which does not need a model.
    """

    @pytest.mark.parametrize(("emitted", "message", "expected"), [
        ({"max": 3000000}, "up to $30M", {"max": 30000000}),
        ({"max": 1500000}, "up to $150M", {"max": 150000000}),
        ({"max": 900000}, "up to $9M", {"max": 9000000}),
        ({"max": 1250000}, "$12.5M ceiling", {"max": 12500000}),
        # No M-notation at all: eight plain digits still come back one zero short.
        ({"max": 4500000}, "no more than $45,000,000", {"max": 45000000}),
        ({"max": 3000000}, "budget is 30 million dollars", {"max": 30000000}),
    ])
    def test_a_bound_short_by_a_power_of_ten_is_resized(self, emitted, message, expected):
        assert correct_bound_direction({"price": emitted}, message) == {"price": expected}

    def test_both_ends_of_a_range_are_resized(self):
        """The reported message. Both bounds land 10x low, and both are recoverable."""
        assert correct_bound_direction(
            {"price": {"min": 3000000, "max": 4000000}}, "from $30M to $40M"
        ) == {"price": {"min": 30000000, "max": 40000000}}

    def test_a_correct_figure_is_untouched(self):
        value = {"price": {"max": 3000000}}
        assert correct_bound_direction(value, "up to $3M") == value

    def test_a_message_stating_both_magnitudes_is_untouched(self):
        """"$3M" and "$30M" are both present, so neither bound is missing its figure."""
        value = {"price": {"min": 3000000, "max": 30000000}}
        assert correct_bound_direction(value, "between $3M and $30M") == value

    def test_a_unit_conversion_is_not_a_magnitude_slip(self):
        """1,500 square yards is 13,500 sqft, and the model is right to say so.

        The digits differ -- "135" against "15" -- which is what keeps the one figure the
        model is *supposed* to transform out of reach of this correction.
        """
        value = {"size_sqft": {"min": 13500, "max": 13500}}
        assert correct_bound_direction(value, "1500 yard") == value

    def test_a_figure_the_parser_cannot_read_still_stands(self):
        value = {"price": {"max": 500000}}
        assert correct_bound_direction(value, "up to half a million") == value

    def test_a_second_field_with_different_digits_does_not_interfere(self):
        """The common mixed message: the size figure shares no digits with the budget."""
        assert correct_bound_direction(
            {"price": {"max": 3000000}, "size_sqft": {"min": 2000, "max": 2000}},
            "we need 2,000 sqft and the budget goes up to $30M",
        ) == {"price": {"max": 30000000}, "size_sqft": {"min": 2000, "max": 2000}}

    def test_two_candidates_mean_the_message_cannot_say(self):
        """Both 300 and 30000000 share the digits "3", so neither is chosen.

        The model's own answer then stands, per the rule above: a bound matching no figure
        at all is left alone rather than dropped, because the model may have normalised
        something the parser cannot read. So this message stays wrong -- deliberately.
        Guessing between two candidates would turn it wrong in a *different* way, and one
        of those two errors is recoverable by asking again.
        """
        assert correct_bound_direction(
            {"price": {"max": 3000000}}, "300 sqft minimum, budget up to $30M"
        ) == {"price": {"max": 3000000}}

    def test_a_resized_bound_still_takes_its_own_comparator(self):
        """Resizing and side-correction compose: "$30M" here is a floor, not a ceiling."""
        assert correct_bound_direction(
            {"price": {"max": 3000000}}, "nothing below $30M"
        ) == {"price": {"min": 30000000}}

    def test_a_resized_bound_is_an_integer(self):
        """The model emits ints; a float here would change the stored JSON shape."""
        result = correct_bound_direction({"price": {"max": 3000000}}, "up to $30M")
        assert isinstance(result["price"]["max"], int)
