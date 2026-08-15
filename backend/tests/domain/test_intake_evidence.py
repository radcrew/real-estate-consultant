"""Tests for dropping answers the user's message contains no evidence for.

The three filters that run before this one validate against the schema and never read the
message, so a configured option word invented from nothing passes all of them. This one
asks the message — differently for a location, which is copied, than for a property type,
which is interpreted.
"""

import pytest

from app.domain.intake_criteria import drop_unevidenced_values

# Shaped like the live rows: options are {label, value} dicts, not plain strings.
QUESTIONS = [
    {"key": "location", "type": "location", "title": "Location", "options": None},
    {"key": "property_type", "type": "multi-select", "title": "Property Type", "options": [
        {"label": "Industrial", "value": "industrial"},
        {"label": "Retail", "value": "retail"},
        {"label": "Flex", "value": "flex"},
        {"label": "Land", "value": "land"},
        {"label": "Office", "value": "office"},
        {"label": "Multifamily", "value": "multifamily"},
        {"label": "Specialty", "value": "specialty"},
    ]},
    {"key": "size_sqft", "type": "range", "title": "Size", "options": {"unit": "FT"}},
]


def _clean(extracted, message, current=None):
    return drop_unevidenced_values(extracted, QUESTIONS, message, current)


class TestLocationIsCopiedNotReasoned:
    def test_a_place_the_message_never_names_is_dropped(self):
        assert _clean({"location": "Chicago"}, "a warehouse with 20 dock doors") == {}

    def test_a_place_the_message_names_is_kept(self):
        assert _clean(
            {"location": "Chicago"}, "a warehouse in Chicago"
        ) == {"location": "Chicago"}

    def test_expanding_what_the_user_gave_is_the_model_doing_its_job(self):
        """"Austin" answered as "Austin, Texas" — only one part is in the text."""
        assert _clean(
            {"location": "Austin, Texas"}, "somewhere in Austin under $2M"
        ) == {"location": "Austin, Texas"}

    def test_a_postal_abbreviation_supports_the_state_it_stands_for(self):
        """The reported message. "TX" is the only place word it contains."""
        assert _clean(
            {"location": "Texas"},
            "I am gonna find a shop which is located in TX, costs more than $1M",
        ) == {"location": "Texas"}

    def test_a_state_name_supports_its_abbreviation(self):
        assert _clean({"location": "CA"}, "an office in California") == {"location": "CA"}

    def test_initials_support_a_two_word_city(self):
        assert _clean(
            {"location": "San Francisco"}, "retail space in SF"
        ) == {"location": "San Francisco"}

    def test_punctuation_does_not_separate_a_name_from_itself(self):
        assert _clean(
            {"location": "St. Louis, MO"}, "a shop in St Louis"
        ) == {"location": "St. Louis, MO"}

    def test_one_distinctive_word_is_enough(self):
        """"Downtown Austin" is not in the text; "Austin" is, and identifies the place."""
        assert _clean(
            {"location": "Downtown Austin"}, "a shop in Austin"
        ) == {"location": "Downtown Austin"}

    def test_a_generic_word_shared_with_the_message_is_not_enough(self):
        """"City" carries no identity, so "Kansas City" is not evidenced by "the city"."""
        assert _clean({"location": "Kansas City"}, "a shop in the city centre") == {}

    def test_a_place_carried_from_an_earlier_turn_survives_a_silent_message(self):
        assert _clean(
            {"location": "Dallas"}, "make it 5,000 sqft", {"location": "Dallas"}
        ) == {"location": "Dallas"}

    def test_a_correction_still_replaces_the_carried_place(self):
        assert _clean(
            {"location": "Houston"}, "actually make it Houston", {"location": "Dallas"}
        ) == {"location": "Houston"}


class TestPropertyTypeIsInterpretedNotCopied:
    """The check abstains unless the message names a type. See ``_type_support``."""

    @pytest.mark.parametrize(("message", "expected"), [
        ("a depot for our trucks", "industrial"),
        ("cold storage facility", "industrial"),
        ("a boutique on the high street", "retail"),
        ("an empty parcel to build on", "land"),
        ("desk space for twenty people", "office"),
        ("a building with twelve flats", "multifamily"),
    ])
    def test_a_generalisation_the_tables_cannot_see_is_left_alone(self, message, expected):
        """None of these words is in any vocabulary we have, and every one is correct.

        A check that required the answer to appear in the message would delete all six.
        Measured on the eval set, that is 7 of 35 correct property types.
        """
        assert _clean({"property_type": [expected]}, message) == {"property_type": [expected]}

    def test_a_type_the_message_names_is_kept(self):
        assert _clean(
            {"property_type": ["industrial"]}, "a warehouse in Dallas"
        ) == {"property_type": ["industrial"]}

    def test_a_second_type_nobody_asked_for_is_dropped(self):
        """Measured in production: "warehouse, restaurant, shop" and its neighbours came
        back carrying types the message never names."""
        assert _clean(
            {"property_type": ["industrial", "retail"]}, "a warehouse in Dallas"
        ) == {"property_type": ["industrial"]}

    def test_both_types_survive_when_the_message_names_both(self):
        assert _clean(
            {"property_type": ["industrial", "retail"]}, "a warehouse or a shop"
        ) == {"property_type": ["industrial", "retail"]}

    def test_the_key_goes_when_no_chosen_type_is_named(self):
        assert _clean({"property_type": ["office"]}, "a warehouse in Dallas") == {}

    def test_a_type_carried_from_an_earlier_turn_survives(self):
        """"Add flex to that as well" names flex and not industrial, and a multi-select
        replaces wholesale on merge — so dropping the carried type would delete it."""
        assert _clean(
            {"property_type": ["industrial", "flex"]},
            "Add flex to that as well",
            {"property_type": ["industrial"]},
        ) == {"property_type": ["industrial", "flex"]}

    def test_the_option_word_itself_counts_as_naming(self):
        assert _clean(
            {"property_type": ["retail"]}, "I want retail in Austin"
        ) == {"property_type": ["retail"]}

    @pytest.mark.parametrize("wording", [
        "high-rise residence", "mixed-use development", "low-income housing",
        "dormitory-style living", "multi-unit property",
    ])
    def test_a_hyphenated_wording_still_matches(self, wording):
        """Punctuation is stripped from the message, so it must be stripped from the
        table too. Without that these five all read as unnamed, and a correct multifamily
        was dropped whenever the message named some other type as well."""
        assert _clean(
            {"property_type": ["multifamily", "industrial"]},
            f"a {wording} next to a warehouse",
        ) == {"property_type": ["multifamily", "industrial"]}


class TestGenericWordsDoNotTriggerTheCheck:
    @pytest.mark.parametrize("word", ["property", "site", "estate", "lot", "downtown"])
    def test_a_structure_noun_does_not_make_the_message_name_a_type(self, word):
        """Bare "property" is listed under land, and almost every enquiry contains one.

        Letting it trigger would rule out every type on "a commercial property for my
        bakery" — a message that says nothing about industrial versus retail.
        """
        assert _clean(
            {"property_type": ["retail"]}, f"a commercial {word} for my bakery"
        ) == {"property_type": ["retail"]}

    def test_it_still_supports_the_type_it_belongs_to(self):
        assert _clean(
            {"property_type": ["land"]}, "an estate with a workshop on it"
        ) == {"property_type": ["land"]}


class TestUntouchedFields:
    def test_a_field_the_questionnaire_does_not_configure_is_left_alone(self):
        assert _clean(
            {"tenure": "lease"}, "a warehouse for lease"
        ) == {"tenure": "lease"}

    def test_ranges_are_left_to_the_bounds_corrector(self):
        assert _clean(
            {"size_sqft": {"min": 5000}}, "a warehouse in Dallas"
        ) == {"size_sqft": {"min": 5000}}

    def test_an_empty_message_asserts_nothing(self):
        value = {"location": "Chicago", "property_type": ["office"]}
        assert _clean(value, "") == value

    def test_a_questionnaire_offering_other_choices_is_not_measured_against_types(self):
        """The check keys off the configured values, not the field name."""
        rows = [{"key": "property_type", "type": "multi-select", "options": [
            {"label": "Class A", "value": "class_a"}, {"label": "Class B", "value": "class_b"},
        ]}]
        assert drop_unevidenced_values(
            {"property_type": ["class_a"]}, rows, "a warehouse in Dallas"
        ) == {"property_type": ["class_a"]}
