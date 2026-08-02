from app.tools._common import (
    compact_property,
    compact_search_response,
    error_text,
    ok_text,
)


def test_ok_text_serializes_dict() -> None:
    result = ok_text({"message": "pong"})
    assert "content" in result
    assert "pong" in result["content"][0]["text"]


def test_error_text_sets_flag() -> None:
    result = error_text("boom")
    assert result["isError"] is True
    assert result["content"][0]["text"] == "boom"


def test_compact_search_response() -> None:
    raw = {
        "criteria": {
            "location": {
                "type": "text",
                "label": "Location",
                "unit": None,
                "data": "Austin",
            },
        },
        "total": 1,
        "limit": 10,
        "offset": 0,
        "results": [
            {
                "property": {
                    "id": "p1",
                    "address": "1 Main",
                    "city": "Austin",
                    "state": "TX",
                    "price": 100,
                    "listing_broker_name": "Ada",
                },
                "match_score": 88.5,
            },
        ],
    }
    out = compact_search_response(raw)
    assert out["total"] == 1
    assert out["results"][0]["property_id"] == "p1"
    assert out["results"][0]["match_score"] == 88.5
    assert out["results"][0]["broker"] == "Ada"
    assert "description" not in out["results"][0]


def test_compact_property() -> None:
    prop = compact_property({"id": "x", "city": "Dallas", "extra": "drop-me"})
    assert prop["property_id"] == "x"
    assert "extra" not in prop


def test_compact_similar_response() -> None:
    from app.tools._common import compact_similar_response

    out = compact_similar_response(
        {
            "results": [
                {
                    "property": {"id": "s1", "city": "Austin", "description": "long"},
                    "match_score": 88.0,
                }
            ],
            "limit": 6,
        },
    )
    assert out["count"] == 1
    assert out["limit"] == 6
    assert out["results"][0]["property_id"] == "s1"
    assert out["results"][0]["match_score"] == 88.0
    assert "description" not in out["results"][0]
