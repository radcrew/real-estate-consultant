from app.utils.listings import format_listing_type_label

_KNOWN_CODES = [
    "LandForAuction",
    "LandForSale",
    "PropertyForSale",
    "CommercialPortfolioForAuction",
    "CommercialPortfolioForSale",
    "ConsolidatedCondosForSale",
]


class TestFormatListingTypeLabel:
    def test_none_returns_none(self):
        assert format_listing_type_label(None) is None

    def test_empty_string_returns_none(self):
        assert format_listing_type_label("") is None

    def test_whitespace_only_returns_none(self):
        assert format_listing_type_label("   ") is None

    def test_known_codes_mapped_to_label(self):
        assert format_listing_type_label("LandForSale") == "Land for sale"
        assert format_listing_type_label("PropertyForSale") == "Property for sale"
        assert format_listing_type_label("LandForAuction") == "Land for auction"

    def test_unknown_code_returned_as_is(self):
        assert format_listing_type_label("ForLease") == "ForLease"

    def test_all_known_codes_have_distinct_labels(self):
        labels = [format_listing_type_label(c) for c in _KNOWN_CODES]
        assert all(label is not None for label in labels)
        assert all(label != code for label, code in zip(labels, _KNOWN_CODES))
        assert len(set(labels)) == len(_KNOWN_CODES)
