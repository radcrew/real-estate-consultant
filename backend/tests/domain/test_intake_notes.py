"""Tests for explaining what the system did to the user's own words.

The reported case: "I need a 100k yard farm" stored 900,000 sq ft and answered "You're
all set!". The conversion is right and there is no way for the person who typed it to
know that, so the working feature read as a broken one.
"""

from __future__ import annotations

import pytest

from app.domain.intake_notes import explain_extraction

QUESTIONS = [
    {"key": "location", "type": "location", "title": "Location"},
    {"key": "property_type", "type": "multi-select", "title": "Property Type"},
    {"key": "price", "type": "range", "title": "Budget"},
    {"key": "size_sqft", "type": "range", "title": "Size"},
]


def _explain(message, before, after=None):
    return explain_extraction(message, before, after if after is not None else before, QUESTIONS)


def _kinds(notes):
    return [note["kind"] for note in notes]


def _text(notes):
    return " ".join(note["message"] for note in notes)


class TestUnitConversion:
    def test_the_reported_message_explains_itself(self):
        """"100k yard" is 900,000 sq ft, and the user should not have to work that out."""
        notes = _explain("I need a 100k yard farm", {"size_sqft": {"min": 900000, "max": 900000}})
        assert _kinds(notes) == ["converted"]
        message = notes[0]["message"]
        assert "100,000 square yards" in message
        assert "900,000 sq ft" in message
        assert "9 sq ft per square yard" in message

    @pytest.mark.parametrize(("message", "stored", "expected"), [
        ("1500 sq metres of office space", 16146, "square metres"),
        ("5 acres of land", 217800, "acres"),
        ("2,000 sq yd retail", 18000, "square yards"),
    ])
    def test_every_convertible_unit_is_explained(self, message, stored, expected):
        notes = _explain(message, {"size_sqft": {"max": stored}})
        assert _kinds(notes) == ["converted"]
        assert expected in notes[0]["message"]

    def test_a_size_already_in_square_feet_says_nothing(self):
        """Explaining the ordinary buries the line that matters."""
        assert _explain("a warehouse under 5000 sqft", {"size_sqft": {"max": 5000}}) == []

    def test_a_rounded_metric_conversion_is_still_recognised(self):
        """1,500 x 10.7639 is 16,145.85, and the model stores a whole number."""
        assert _kinds(_explain("1500 sq m", {"size_sqft": {"max": 16146}})) == ["converted"]

    def test_a_size_that_is_not_the_conversion_is_not_claimed_to_be(self):
        """The arithmetic is checked against both sides before anything is asserted."""
        assert _explain("a 100k yard farm", {"size_sqft": {"max": 100000}}) == []

    def test_a_unit_this_cannot_convert_says_nothing(self):
        assert _explain("32ft clear height", {"size_sqft": {"max": 32}}) == []


class TestFiguresThatBelongElsewhere:
    def test_a_size_read_as_a_budget_is_explained_away(self):
        """The user asked no price question, so the missing budget needs a reason."""
        notes = _explain(
            "I need a 100k sqft warehouse in Chicago",
            {"size_sqft": {"min": 100000}, "price": {"min": 100000}},
            {"size_sqft": {"min": 100000}},
        )
        assert _kinds(notes) == ["reassigned"]
        assert "100,000" in notes[0]["message"]
        assert "is a size, not a budget" in notes[0]["message"]

    def test_it_names_the_field_the_way_the_questionnaire_does(self):
        """"your Size", not "your size_sqft" -- a column name leaking into a sentence."""
        notes = _explain(
            "a 100k sqft warehouse",
            {"size_sqft": {"min": 100000}, "price": {"min": 100000}},
            {"size_sqft": {"min": 100000}},
        )
        assert "recorded as your Size" in notes[0]["message"]

    def test_a_dock_count_read_as_a_size_is_explained(self):
        notes = _explain(
            "office in Boise, 3 floors", {"size_sqft": {"max": 3}}, {},
        )
        assert _kinds(notes) == ["reassigned"]
        assert "is a count" in notes[0]["message"]

    def test_a_budget_the_message_supports_is_not_explained_away(self):
        value = {"price": {"max": 2000000}}
        assert _explain("under $2M", value, value) == []


class TestCorrections:
    def test_a_bound_the_wording_moved_is_explained(self):
        notes = _explain(
            "cost should be lower than $2M", {"price": {"min": 2000000}},
            {"price": {"max": 2000000}},
        )
        assert _kinds(notes) == ["moved"]
        assert "upper limit" in notes[0]["message"]

    def test_a_lower_bound_says_lower(self):
        notes = _explain(
            "nothing below 8,000 sqft", {"size_sqft": {"max": 8000}},
            {"size_sqft": {"min": 8000}},
        )
        assert "lower limit" in _text(notes)

    def test_a_magnitude_the_message_settled_is_explained(self):
        notes = _explain("up to $30M", {"price": {"max": 3000000}}, {"price": {"max": 30000000}})
        assert _kinds(notes) == ["resized"]
        assert "30,000,000" in notes[0]["message"]

    def test_an_untouched_bound_says_nothing(self):
        value = {"price": {"max": 3000000}}
        assert _explain("up to $3M", value, value) == []


class TestQuiet:
    def test_a_message_with_no_figures_says_nothing(self):
        assert _explain("a warehouse in Dallas", {"location": "Dallas"}) == []

    def test_an_empty_message_says_nothing(self):
        assert _explain("", {"size_sqft": {"max": 5000}}) == []

    def test_the_ordinary_turn_is_silent(self):
        """Most turns. If this ever starts producing notes, the feature is broken."""
        value = {"location": "Austin", "property_type": ["industrial"],
                 "size_sqft": {"max": 5000}, "price": {"max": 2000000}}
        assert _explain("industrial in Austin, under 5000 sqft and under $2M", value) == []

    def test_notes_carry_the_field_they_are_about(self):
        notes = _explain("a 100k yard farm", {"size_sqft": {"max": 900000}})
        assert notes[0]["field"] == "size_sqft"

    def test_missing_questions_still_produce_a_readable_note(self):
        notes = explain_extraction(
            "a 100k sqft warehouse",
            {"size_sqft": {"min": 100000}, "price": {"min": 100000}},
            {"size_sqft": {"min": 100000}},
        )
        assert "size sqft" in notes[0]["message"]
