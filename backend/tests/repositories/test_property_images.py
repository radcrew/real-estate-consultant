from app.repositories.property_images import get_first_image_url, list_all_image_urls
from tests.repositories.conftest import make_supabase_client

_PROPERTY_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class TestGetFirstImageUrl:
    async def test_returns_first_url(self):
        client = make_supabase_client([{"url": "https://example.com/1.jpg"}])
        result = await get_first_image_url(client, _PROPERTY_ID)
        assert result == "https://example.com/1.jpg"

    async def test_returns_none_when_no_rows(self):
        client = make_supabase_client([])
        result = await get_first_image_url(client, _PROPERTY_ID)
        assert result is None

    async def test_returns_none_when_url_is_blank(self):
        client = make_supabase_client([{"url": "   "}])
        result = await get_first_image_url(client, _PROPERTY_ID)
        assert result is None


class TestListAllImageUrls:
    async def test_returns_all_urls(self):
        client = make_supabase_client(
            [{"url": "https://example.com/1.jpg"}, {"url": "https://example.com/2.jpg"}],
        )
        result = await list_all_image_urls(client, _PROPERTY_ID)
        assert result == ["https://example.com/1.jpg", "https://example.com/2.jpg"]

    async def test_skips_blank_urls(self):
        client = make_supabase_client([{"url": "https://example.com/1.jpg"}, {"url": "  "}])
        result = await list_all_image_urls(client, _PROPERTY_ID)
        assert result == ["https://example.com/1.jpg"]

    async def test_returns_empty_list_when_no_rows(self):
        client = make_supabase_client([])
        result = await list_all_image_urls(client, _PROPERTY_ID)
        assert result == []
