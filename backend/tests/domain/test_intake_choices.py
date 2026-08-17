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

    def test_a_repeated_choice_is_stored_once(self):
        """Reported: "warehouse, restaurant, shop" stored industrial, retail, retail.

        Two of the three phrasings are the same type, and the model is right to emit both
        -- it is reading three things the client named. The repeat has to die here.
        """
        assert _clean({"property_type": ["Industrial", "Retail", "Retail"]}) == {
            "property_type": ["Industrial", "Retail"]
        }

    def test_spellings_that_canonicalise_together_collapse(self):
        """Canonicalisation is what creates the duplicate, so case must collapse too."""
        assert _clean({"property_type": ["retail", "RETAIL", "Retail"]}) == {
            "property_type": ["Retail"]
        }

    def test_deduping_preserves_the_order_the_client_said_them_in(self):
        result = _clean({"property_type": ["Flex", "Office", "flex", "Retail"]})
        assert result["property_type"] == ["Flex", "Office", "Retail"]

    def test_a_repeated_option_dump_is_still_a_dump(self):
        """Dedup must not let the schema-copy through by making the set look shorter."""
        assert _clean({"property_type": ["Office", "Office", "Retail", "Industrial",
                                         "Warehouse", "Flex", "Land"]}) == {}


class TestDatabaseOptionShape:
    """The live rows store options as {"label": ..., "value": ...}, not plain strings.

    Reading only the string form made this filter a silent no-op in production: every DB
    option is a dict, so nothing was recognised and every value passed through.
    """

    DB_QUESTIONS = [
        {"key": "property_type", "type": "multi-select", "options": [
            {"label": "Industrial", "value": "industrial"},
            {"label": "Office", "value": "office"},
            {"label": "Retail", "value": "retail"},
        ]},
    ]

    def _clean_db(self, extracted):
        return drop_unconfigured_choices(extracted, self.DB_QUESTIONS)

    def test_drops_a_choice_that_is_not_offered(self):
        assert self._clean_db({"property_type": ["Building"]}) == {}

    def test_matches_on_the_label(self):
        assert self._clean_db({"property_type": ["Industrial"]}) == {
            "property_type": ["industrial"]
        }

    def test_matches_on_the_value(self):
        assert self._clean_db({"property_type": ["industrial"]}) == {
            "property_type": ["industrial"]
        }

    def test_stores_the_value_spelling(self):
        """Search compares property_type with ilike, so casing does not affect matching."""
        assert self._clean_db({"property_type": ["RETAIL"]}) == {"property_type": ["retail"]}

    def test_still_catches_the_option_dump(self):
        assert self._clean_db({"property_type": ["Industrial", "Office", "Retail"]}) == {}


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
