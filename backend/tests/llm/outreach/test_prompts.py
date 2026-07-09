from app.llm.outreach.prompts import (
    build_outreach_user_message,
    format_listing_block_for_outreach,
    format_sender_block_for_outreach,
)


class TestFormatListingBlock:
    def test_known_keys_included(self):
        row = {"address": "100 Main St", "city": "Austin", "price": 1_000_000}
        result = format_listing_block_for_outreach(row)
        assert "address: 100 Main St" in result
        assert "city: Austin" in result
        assert "price: 1000000" in result

    def test_none_and_empty_values_skipped(self):
        row = {"address": None, "city": "", "price": 500_000}
        result = format_listing_block_for_outreach(row)
        assert "address" not in result
        assert "city" not in result
        assert "price: 500000" in result

    def test_empty_row_returns_fallback(self):
        assert format_listing_block_for_outreach({}) == "(No listing details provided.)"

    def test_unknown_keys_ignored(self):
        row = {"address": "1 St", "extra_field": "ignored"}
        result = format_listing_block_for_outreach(row)
        assert "extra_field" not in result


class TestFormatSenderBlock:
    def test_profile_fields_included(self):
        profile = {"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"}
        result = format_sender_block_for_outreach(profile_row=profile, auth_email=None)
        assert "first_name: Alice" in result
        assert "email: alice@example.com" in result

    def test_auth_email_used_as_fallback(self):
        result = format_sender_block_for_outreach(profile_row=None, auth_email="user@example.com")
        assert "email: user@example.com" in result

    def test_profile_email_takes_precedence_over_auth_email(self):
        profile = {"email": "profile@example.com"}
        result = format_sender_block_for_outreach(profile_row=profile, auth_email="auth@example.com")
        assert "profile@example.com" in result
        assert "auth@example.com" not in result

    def test_no_sender_info_returns_neutral_fallback(self):
        result = format_sender_block_for_outreach(profile_row=None, auth_email=None)
        assert "neutral sign-off" in result

    def test_profile_none_values_skipped(self):
        profile = {"first_name": None, "last_name": "Smith", "email": ""}
        result = format_sender_block_for_outreach(profile_row=profile, auth_email="u@x.com")
        assert "first_name" not in result
        assert "last_name: Smith" in result


class TestBuildOutreachUserMessage:
    def test_contains_listing_and_sender_sections(self):
        row = {"address": "1 Main St", "city": "Austin"}
        profile = {"first_name": "Bob"}
        result = build_outreach_user_message(property_row=row, profile_row=profile, auth_email=None)
        assert "Listing summary:" in result
        assert "Sender" in result
        assert "1 Main St" in result
        assert "first_name: Bob" in result

    def test_no_profile_uses_fallback_sender(self):
        result = build_outreach_user_message(property_row={}, profile_row=None, auth_email=None)
        assert "neutral sign-off" in result
