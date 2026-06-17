import pytest
from fastapi import HTTPException

from app.utils.supabase.response import as_row_list, expect_single_row, get_single_row


class TestAsRowList:
    def test_dict_wrapped_in_list(self):
        assert as_row_list({"id": 1}) == [{"id": 1}]

    def test_list_of_dicts_returned(self):
        rows = [{"id": 1}, {"id": 2}]
        assert as_row_list(rows) == rows

    def test_non_dict_items_filtered(self):
        assert as_row_list([{"id": 1}, "bad", None, 42]) == [{"id": 1}]

    def test_empty_list_returned(self):
        assert as_row_list([]) == []

    def test_non_list_non_dict_returns_empty(self):
        assert as_row_list(None) == []
        assert as_row_list(42) == []
        assert as_row_list("string") == []


class TestExpectSingleRow:
    def test_dict_returned_directly(self):
        row = {"id": 1}
        assert expect_single_row(row, detail="err") is row

    def test_single_element_list_unwrapped(self):
        row = {"id": 1}
        assert expect_single_row([row], detail="err") is row

    def test_empty_list_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            expect_single_row([], detail="no row")
        assert exc_info.value.status_code == 502

    def test_multi_element_list_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            expect_single_row([{"id": 1}, {"id": 2}], detail="ambiguous")
        assert exc_info.value.status_code == 502

    def test_non_dict_single_element_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            expect_single_row(["not-a-dict"], detail="bad shape")
        assert exc_info.value.status_code == 502

    def test_none_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            expect_single_row(None, detail="missing")
        assert exc_info.value.status_code == 502


class TestGetSingleRow:
    def test_extracts_data_attribute(self):
        class FakeResult:
            data = {"id": 1}

        assert get_single_row(FakeResult(), detail="err") == {"id": 1}

    def test_data_as_single_element_list(self):
        class FakeResult:
            data = [{"id": 1}]

        assert get_single_row(FakeResult(), detail="err") == {"id": 1}

    def test_missing_data_attribute_raises_502(self):
        with pytest.raises(HTTPException) as exc_info:
            get_single_row(object(), detail="no data")
        assert exc_info.value.status_code == 502

    def test_empty_data_raises_502(self):
        class FakeResult:
            data = []

        with pytest.raises(HTTPException) as exc_info:
            get_single_row(FakeResult(), detail="empty")
        assert exc_info.value.status_code == 502
