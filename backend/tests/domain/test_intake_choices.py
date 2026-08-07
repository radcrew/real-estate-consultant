"""Tests for dropping select / multi-select answers the questionnaire does not offer."""

from app.domain.intake_criteria import drop_unconfigured_choices

QUESTIONS = [
    {"key": "location", "type": "location", "options": None},
    {"key": "property_type", "type": "multiselect",
     "options": ["Office", "Retail", "Industrial", "Warehouse", "Flex", "Land"]},
    {"key": "listing_type", "type": "select", "options": ["Sale", "Lease"]},
    {"key": "price", "type": "range", "options": {"unit": "USD"}},
    {"key": "loading_docks", "type": "number", "options": None},
]


def _clean(extracted):
    return drop_unconfigured_choices(extracted, QUESTIONS)


class TestMultiSelect:
    def test_keeps_configured_choices(self):
        assert _clean({"property_type": ["Warehouse", "Flex"]}) == {
            "property_type": ["Warehouse", "Flex"]
        }

    def test_drops_a_choice_that_is_not_offered(self):
        """The reported case: "house" is not a commercial property type."""
        assert _clean({"property_type": ["house"]}) == {}

    def test_keeps_the_valid_part_of_a_mixed_answer(self):
        assert _clean({"property_type": ["house", "Warehouse"]}) == {
            "property_type": ["Warehouse"]
        }

    def test_canonicalises_case(self):
        assert _clean({"property_type": ["warehouse", "FLEX"]}) == {
            "property_type": ["Warehouse", "Flex"]
        }

    def test_coerces_a_bare_string(self):
        assert _clean({"property_type": "Retail"}) == {"property_type": ["Retail"]}

    def test_drops_the_whole_option_list(self):
        """Copying every choice out of the schema is the stock model's signature move."""
        assert _clean({"property_type":
                       ["Office", "Retail", "Industrial", "Warehouse", "Flex", "Land"]}) == {}

    def test_all_but_one_is_a_real_answer(self):
        result = _clean({"property_type": ["Office", "Retail", "Industrial", "Warehouse", "Flex"]})
        assert len(result["property_type"]) == 5


class TestSingleSelect:
    def test_keeps_a_configured_choice(self):
        assert _clean({"listing_type": "Lease"}) == {"listing_type": "Lease"}

    def test_canonicalises_case(self):
        assert _clean({"listing_type": "sale"}) == {"listing_type": "Sale"}

    def test_drops_a_choice_that_is_not_offered(self):
        assert _clean({"listing_type": "Rent"}) == {}

    def test_two_choice_questions_are_never_treated_as_an_option_dump(self):
        """"buy or lease" can legitimately be both; the dump heuristic needs >2 options."""
        assert _clean({"listing_type": "Sale"}) == {"listing_type": "Sale"}


class TestUntouchedFields:
    def test_leaves_free_text_alone(self):
        assert _clean({"location": "Texas"}) == {"location": "Texas"}

    def test_leaves_ranges_alone(self):
        """Range options are a dict ({"unit": "USD"}), not an enumeration."""
        value = {"price": {"max": 2000000}}
        assert _clean(value) == value

    def test_leaves_numbers_alone(self):
        assert _clean({"loading_docks": 3}) == {"loading_docks": 3}

    def test_leaves_unknown_keys_alone(self):
        """Key filtering is the caller's job; this only judges values."""
        assert _clean({"made_up": "x"}) == {"made_up": "x"}

    def test_empty_extraction(self):
        assert _clean({}) == {}

    def test_does_not_mutate_its_input(self):
        original = {"property_type": ["house"]}
        drop_unconfigured_choices(original, QUESTIONS)
        assert original == {"property_type": ["house"]}
