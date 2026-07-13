from app.domain.intake_criteria import (
    normalize_intake_value,
    normalize_merged_criteria,
)


class TestNormalizeIntakeValue:
    # location types
    def test_location_string_stripped(self):
        assert normalize_intake_value("location", "  Austin  ") == "Austin"

    def test_location_dict_joined(self):
        result = normalize_intake_value("geo", {"city": "Austin", "state": "TX", "country": "US"})
        assert result == "Austin, TX, US"

    def test_location_dict_label_fallback(self):
        result = normalize_intake_value("location", {"label": "Downtown Austin"})
        assert result == "Downtown Austin"

    def test_location_dict_empty_falls_back_to_value(self):
        result = normalize_intake_value("location", {})
        assert result == {}

    # multi-select types
    def test_multi_select_string_wrapped(self):
        assert normalize_intake_value("multiselect", "office") == ["office"]

    def test_multi_select_list_cleaned(self):
        assert normalize_intake_value("multi-select", ["office", "  industrial  ", ""]) == ["office", "industrial"]

    def test_multi_select_empty_list(self):
        assert normalize_intake_value("tags", []) == []

    # range types
    def test_range_dict_parsed(self):
        result = normalize_intake_value("range", {"min": "100", "max": "500"})
        assert result == {"min": 100.0, "max": 500.0}

    def test_range_with_unit(self):
        result = normalize_intake_value("range", {"min": 1000, "unit": "sqft"})
        assert result["unit"] == "sqft"

    def test_range_non_dict_returned_as_is(self):
        assert normalize_intake_value("range", "big") == "big"

    # text (default)
    def test_text_returned_unchanged(self):
        assert normalize_intake_value("text", "hello") == "hello"

    def test_unknown_type_returned_unchanged(self):
        assert normalize_intake_value("custom_type", 42) == 42

    def test_multi_select_non_list_non_string_returns_empty(self):
        assert normalize_intake_value("multiselect", 42) == []

    def test_range_invalid_min_max_falls_back_to_original(self):
        # when all keys fail float conversion, original dict is returned unchanged
        original = {"min": "bad", "max": None}
        result = normalize_intake_value("range", original)
        assert result == original

    def test_range_partial_invalid_min_omitted(self):
        result = normalize_intake_value("range", {"min": "bad", "max": 500})
        assert "min" not in result
        assert result["max"] == 500.0


class TestNormalizeMergedCriteria:
    def test_normalizes_matching_keys(self):
        questions = [{"key": "property_type", "type": "multiselect"}]
        result = normalize_merged_criteria(
            {"property_type": "office"},
            questions,
        )
        assert result["property_type"] == ["office"]

    def test_reserved_keys_passed_through(self):
        questions = [{"key": "location", "type": "location"}]
        result = normalize_merged_criteria(
            {"location": "Austin"},
            questions,
            reserved_keys=frozenset({"location"}),
        )
        assert result["location"] == "Austin"

    def test_unknown_key_treated_as_text(self):
        result = normalize_merged_criteria({"notes": "  hi  "}, [])
        assert result["notes"] == "  hi  "

    def test_empty_criteria_returns_empty(self):
        assert normalize_merged_criteria({}, []) == {}
