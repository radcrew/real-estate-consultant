from app.tools._common import error_text, ok_text


def test_ok_text_serializes_dict() -> None:
    result = ok_text({"message": "pong"})
    assert result["content"][0]["type"] == "text"
    assert "pong" in result["content"][0]["text"]
    assert "isError" not in result


def test_error_text_sets_flag() -> None:
    result = error_text("boom")
    assert result["isError"] is True
    assert result["content"][0]["text"] == "boom"
