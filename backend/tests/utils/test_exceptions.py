from app.utils.listings import format_listing_type_label


class TestFormatListingTypeLabel:
    def test_none_returns_none(self):
        assert format_listing_type_label(None) is None

    def test_empty_string_returns_none(self):
        assert format_listing_type_label("") is None

    def test_whitespace_only_returns_none(self):
        assert format_listing_type_label("   ") is None

    def test_known_code_mapped(self):
        assert format_listing_type_label("LandForSale") == "Land for sale"
        assert format_listing_type_label("PropertyForSale") == "Property for sale"

    def test_unknown_code_returned_as_is(self):
        assert format_listing_type_label("ForLease") == "ForLease"

    def test_all_known_codes_have_labels(self):
        codes = [
            "LandForAuction",
            "LandForSale",
            "PropertyForSale",
            "CommercialPortfolioForAuction",
            "CommercialPortfolioForSale",
            "ConsolidatedCondosForSale",
        ]
        for code in codes:
            result = format_listing_type_label(code)
            assert result is not None
            assert result != code  # mapped, not raw
