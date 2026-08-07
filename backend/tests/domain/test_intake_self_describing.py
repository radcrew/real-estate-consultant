"""Tests for dropping answers that describe the field instead of answering it."""

import pytest

from app.domain.intake_criteria import drop_self_describing_values

# Shaped like the live rows: options are {label, value} dicts, not plain strings.
QUESTIONS = [
    {"key": "location", "type": "location", "title": "Location", "options": None},
    {"key": "property_type", "type": "multi-select", "title": "Property Type", "options": [
        {"label": "Industrial", "value": "industrial"},
        {"label": "Retail", "value": "retail"},
        {"label": "Flex", "value": "flex"},
    ]},
    {"key": "size_sqft", "type": "range", "title": "Size", "options": {"unit": "FT"}},
]


def _clean(extracted):
    return drop_self_describing_values(extracted, QUESTIONS)


class TestGenericNouns:
    @pytest.mark.parametrize(
        "noun",
        ["Building", "building", "  BUILDING ", "property", "space", "house",
         "site", "premises", "commercial property", "real estate"],
    )
    def test_a_bare_structure_noun_is_not_a_location(self, noun):
        """The reported case: "I am finding a building..." set location to "Building"."""
        assert _clean({"location": noun}) == {}


class TestFieldLabelEcho:
    @pytest.mark.parametrize("echo", ["Location", "location", "LOCATION"])
    def test_the_questions_own_name_is_not_an_answer(self, echo):
        assert _clean({"location": echo}) == {}

    def test_the_key_with_underscores_spelled_out(self):
        rows = [{"key": "size_sqft", "type": "text", "title": "Size", "options": None}]
        assert drop_self_describing_values({"size_sqft": "size sqft"}, rows) == {}


class TestPropertyTypeInTheLocationSlot:
    @pytest.mark.parametrize(
        "value", ["industrial", "Industrial", "industrial space", "Retail property", "flex unit"],
    )
    def test_a_property_type_is_not_a_location(self, value):
        assert _clean({"location": value}) == {}


class TestRealValuesSurvive:
    @pytest.mark.parametrize(
        "place",
        ["Austin, Texas", "Building Heights", "Commercial", "Spacehill",
         "Houston", "Property Lane, Dallas", "TX"],
    )
    def test_place_names_are_untouched(self, place):
        """Matching is exact, never substring — "Building Heights" is a real address."""
        assert _clean({"location": place}) == {"location": place}

    def test_other_fields_are_untouched(self):
        value = {"property_type": ["industrial"], "size_sqft": {"min": 100}}
        assert _clean(value) == value

    def test_a_property_type_answering_its_own_question_is_kept(self):
        """The rule is location-specific; "industrial" is a fine property_type."""
        assert _clean({"property_type": "industrial"}) == {"property_type": "industrial"}

    def test_unknown_keys_are_untouched(self):
        assert _clean({"made_up": "Building"}) == {"made_up": "Building"}

    def test_empty_extraction(self):
        assert _clean({}) == {}

    def test_does_not_mutate_its_input(self):
        original = {"location": "Building"}
        drop_self_describing_values(original, QUESTIONS)
        assert original == {"location": "Building"}
