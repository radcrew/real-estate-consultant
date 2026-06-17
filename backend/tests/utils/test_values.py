from app.utils.values import clean_str_or_none, float_or_none


class TestCleanStrOrNone:
    def test_none_returns_none(self):
        assert clean_str_or_none(None) is None

    def test_empty_string_returns_none(self):
        assert clean_str_or_none("") is None

    def test_whitespace_only_returns_none(self):
        assert clean_str_or_none("   ") is None

    def test_strips_surrounding_whitespace(self):
        assert clean_str_or_none("  hello  ") == "hello"

    def test_plain_string_returned(self):
        assert clean_str_or_none("Austin") == "Austin"

    def test_non_string_coerced(self):
        assert clean_str_or_none(42) == "42"

    def test_zero_coerced_to_string(self):
        assert clean_str_or_none(0) == "0"


class TestFloatOrNone:
    def test_none_returns_none(self):
        assert float_or_none(None) is None

    def test_integer_converted(self):
        assert float_or_none(5) == 5.0

    def test_string_number_converted(self):
        assert float_or_none("3.14") == 3.14

    def test_invalid_string_returns_none(self):
        assert float_or_none("abc") is None

    def test_empty_string_returns_none(self):
        assert float_or_none("") is None

    def test_zero_returns_zero(self):
        assert float_or_none(0) == 0.0

    def test_negative_number(self):
        assert float_or_none(-10.5) == -10.5
