"""Tests for loopnet_seed connector parsing helpers and normalize logic."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.connectors.loopnet_seed import (
    LoopNetSeedConnector,
    _best_price,
    _best_property_type,
    _best_size_sqft,
    _implied_clear_height,
    _implied_loading_docks,
    _implied_monthly_rent,
    _normalize,
    _parse_images,
    _parse_money_string,
    _parse_property,
    _parse_simple_float,
    _parse_size_sqft,
    _strip_leading_currency,
    _take_leading_number,
    _to_float,
)
from app.connectors.base import IngestionReport


# ---------------------------------------------------------------------------
# _parse_simple_float
# ---------------------------------------------------------------------------

class TestParseSimpleFloat:
    def test_basic_integer(self):
        assert _parse_simple_float("42") == 42.0

    def test_decimal(self):
        assert _parse_simple_float("3.14") == 3.14

    def test_with_commas(self):
        assert _parse_simple_float("1,000,000") == 1_000_000.0

    def test_negative(self):
        assert _parse_simple_float("-5.5") == -5.5

    def test_empty_string_returns_none(self):
        assert _parse_simple_float("") is None

    def test_whitespace_only_returns_none(self):
        assert _parse_simple_float("   ") is None

    def test_stops_at_non_numeric(self):
        assert _parse_simple_float("100 sqft") == 100.0

    def test_lone_dot_returns_none(self):
        assert _parse_simple_float(".") is None

    def test_only_dot_after_stripping_returns_none(self):
        assert _parse_simple_float(",") is None


# ---------------------------------------------------------------------------
# _strip_leading_currency / _parse_money_string
# ---------------------------------------------------------------------------

class TestStripLeadingCurrency:
    def test_strips_dollar(self):
        assert _strip_leading_currency("$1,000") == "1,000"

    def test_strips_pound(self):
        assert _strip_leading_currency("£500") == "500"

    def test_strips_euro(self):
        assert _strip_leading_currency("€250") == "250"

    def test_no_symbol_unchanged(self):
        assert _strip_leading_currency("1000") == "1000"

    def test_strips_whitespace_too(self):
        assert _strip_leading_currency("  $99  ") == "99"


class TestParseMoneyString:
    def test_dollar_amount(self):
        assert _parse_money_string("$1,500,000") == 1_500_000.0

    def test_plain_number(self):
        assert _parse_money_string("250000") == 250_000.0

    def test_empty_returns_none(self):
        assert _parse_money_string("") is None

    def test_only_symbol_returns_none(self):
        assert _parse_money_string("$") is None


# ---------------------------------------------------------------------------
# _take_leading_number
# ---------------------------------------------------------------------------

class TestTakeLeadingNumber:
    def test_integer_with_tail(self):
        value, tail = _take_leading_number("1000 SF")
        assert value == 1000.0
        assert "SF" in tail

    def test_decimal(self):
        value, tail = _take_leading_number("2.5 acres")
        assert value == 2.5

    def test_empty_string(self):
        value, tail = _take_leading_number("")
        assert value is None

    def test_non_numeric_start(self):
        value, tail = _take_leading_number("N/A")
        assert value is None

    def test_commas_ignored(self):
        value, tail = _take_leading_number("10,000 sqft")
        assert value == 10_000.0


# ---------------------------------------------------------------------------
# _parse_size_sqft
# ---------------------------------------------------------------------------

class TestParseSizeSqft:
    def test_sqft_suffix(self):
        assert _parse_size_sqft("5000 SF") == 5000.0

    def test_square_feet(self):
        assert _parse_size_sqft("5,000 Square Feet") == 5000.0

    def test_acres_converted(self):
        result = _parse_size_sqft("2 acres")
        assert result == pytest.approx(2 * 43_560.0)

    def test_sqft_compact(self):
        assert _parse_size_sqft("12000sqft") == 12000.0

    def test_empty_returns_none(self):
        assert _parse_size_sqft("") is None

    def test_no_unit_returns_none(self):
        assert _parse_size_sqft("500 units") is None

    def test_acre_abbreviation(self):
        result = _parse_size_sqft("1.5 ac")
        assert result == pytest.approx(1.5 * 43_560.0)


# ---------------------------------------------------------------------------
# _to_float
# ---------------------------------------------------------------------------

class TestToFloat:
    def test_int(self):
        assert _to_float(5) == 5.0

    def test_float(self):
        assert _to_float(3.14) == 3.14

    def test_string_number(self):
        assert _to_float("42") == 42.0

    def test_none_returns_none(self):
        assert _to_float(None) is None

    def test_bool_returns_none(self):
        assert _to_float(True) is None

    def test_non_numeric_string_returns_none(self):
        assert _to_float("N/A") is None

    def test_empty_string_returns_none(self):
        assert _to_float("") is None


# ---------------------------------------------------------------------------
# _best_size_sqft
# ---------------------------------------------------------------------------

class TestBestSizeSqft:
    def test_uses_squareFootage_numeric(self):
        assert _best_size_sqft({"squareFootage": 10000}) == 10000.0

    def test_uses_propertyFacts_total_building_size(self):
        result = _best_size_sqft({"propertyFacts": {"TotalBuildingSize": "8,000 SF"}})
        assert result == 8000.0

    def test_uses_summary_buildingSize(self):
        result = _best_size_sqft({"summary": {"buildingSize": "5000 sqft"}})
        assert result == 5000.0

    def test_uses_buildingSize_string(self):
        result = _best_size_sqft({"buildingSize": "3000 SF"})
        assert result == 3000.0

    def test_returns_none_when_no_data(self):
        assert _best_size_sqft({}) is None


# ---------------------------------------------------------------------------
# _best_price
# ---------------------------------------------------------------------------

class TestBestPrice:
    def test_uses_priceNumeric(self):
        assert _best_price({"priceNumeric": 500000}) == 500000.0

    def test_uses_price_string(self):
        assert _best_price({"price": "$1,200,000"}) == 1_200_000.0

    def test_uses_propertyFacts_Price(self):
        assert _best_price({"propertyFacts": {"Price": "$750,000"}}) == 750_000.0

    def test_returns_none_when_no_data(self):
        assert _best_price({}) is None


# ---------------------------------------------------------------------------
# _best_property_type
# ---------------------------------------------------------------------------

class TestBestPropertyType:
    def test_uses_propertyType_field(self):
        assert _best_property_type({"propertyType": "Industrial"}) == "Industrial"

    def test_falls_back_to_propertyTypeDetailed(self):
        assert _best_property_type({"propertyTypeDetailed": "Warehouse"}) == "Warehouse"

    def test_uses_summary_propertyType(self):
        result = _best_property_type({"summary": {"propertyType": "Office"}})
        assert result == "Office"

    def test_uses_propertyFacts(self):
        result = _best_property_type({"propertyFacts": {"PropertyType": "Retail"}})
        assert result == "Retail"

    def test_returns_none_when_no_data(self):
        assert _best_property_type({}) is None


# ---------------------------------------------------------------------------
# Implied value helpers
# ---------------------------------------------------------------------------

class TestImpliedHelpers:
    def test_monthly_rent_calculated(self):
        assert _implied_monthly_rent(1_200_000.0) == pytest.approx((1_200_000 * 0.05) / 12)

    def test_monthly_rent_none_returns_none(self):
        assert _implied_monthly_rent(None) is None

    def test_clear_height_small_building(self):
        assert _implied_clear_height(10_000.0) == pytest.approx(14.0 + 10_000 / 22_000, rel=1e-3)

    def test_clear_height_capped_at_22(self):
        assert _implied_clear_height(1_000_000.0) == 22.0

    def test_clear_height_none_returns_none(self):
        assert _implied_clear_height(None) is None

    def test_clear_height_zero_returns_none(self):
        assert _implied_clear_height(0.0) is None

    def test_loading_docks_large(self):
        assert _implied_loading_docks(40_000.0) == 2

    def test_loading_docks_small(self):
        assert _implied_loading_docks(10_000.0) == 1

    def test_loading_docks_none(self):
        assert _implied_loading_docks(None) == 1


# ---------------------------------------------------------------------------
# _parse_images
# ---------------------------------------------------------------------------

class TestParseImages:
    def test_returns_image_urls(self):
        listing = {"KVImages": ["https://a.com/1.jpg", "https://a.com/2.jpg"]}
        assert _parse_images(listing) == ["https://a.com/1.jpg", "https://a.com/2.jpg"]

    def test_empty_list_returns_empty(self):
        assert _parse_images({"KVImages": []}) == []

    def test_no_key_returns_empty(self):
        assert _parse_images({}) == []

    def test_non_list_returns_empty(self):
        assert _parse_images({"KVImages": "not-a-list"}) == []

    def test_skips_blank_entries(self):
        assert _parse_images({"KVImages": ["  ", "https://a.com/img.jpg"]}) == ["https://a.com/img.jpg"]


# ---------------------------------------------------------------------------
# _normalize
# ---------------------------------------------------------------------------

class TestNormalize:
    def _listing(self, **kw):
        base = {
            "propertyId": "p-1",
            "address": "100 Main St",
            "city": "Austin",
            "state": "TX",
            "listingType": "Sale",
            "propertyType": "Industrial",
        }
        base.update(kw)
        return base

    def test_valid_listing_normalized(self):
        rows, rejected = _normalize([self._listing()])
        assert len(rows) == 1
        assert rejected == {}

    def test_missing_address_rejected(self):
        listing = self._listing()
        listing.pop("address")
        rows, rejected = _normalize([listing])
        assert len(rows) == 0
        assert rejected.get("missing_address") == 1

    def test_images_attached_when_property_id_present(self):
        listing = self._listing(KVImages=["https://a.com/img.jpg"])
        rows, _ = _normalize([listing])
        prop, images = rows[0]
        assert len(images) == 1
        assert images[0].url == "https://a.com/img.jpg"

    def test_no_images_when_no_property_id(self):
        listing = self._listing(KVImages=["https://a.com/img.jpg"])
        listing.pop("propertyId")
        rows, _ = _normalize([listing])
        prop, images = rows[0]
        assert images == []

    def test_property_id_deterministic(self):
        listing = self._listing()
        rows1, _ = _normalize([listing])
        rows2, _ = _normalize([listing])
        assert rows1[0][0].id == rows2[0][0].id

    def test_multiple_listings(self):
        listings = [
            self._listing(propertyId="a", address="1st St"),
            self._listing(propertyId="b", address="2nd St"),
        ]
        rows, rejected = _normalize(listings)
        assert len(rows) == 2
        assert rejected == {}


# ---------------------------------------------------------------------------
# LoopNetSeedConnector.run
# ---------------------------------------------------------------------------

class TestLoopNetSeedConnectorRun:
    def _make_connector(self):
        mock_client = MagicMock()
        mock_client.table.return_value.delete.return_value.in_.return_value.execute = AsyncMock()
        mock_client.table.return_value.upsert.return_value.execute = AsyncMock()
        mock_client.table.return_value.insert.return_value.execute = AsyncMock()
        return LoopNetSeedConnector(client=mock_client)

    def _dataset(self, listings):
        return json.dumps(listings)

    @pytest.mark.asyncio
    async def test_run_returns_report(self, tmp_path):
        data = [{"propertyId": "x1", "address": "1 Main St", "city": "Austin", "state": "TX"}]
        dataset = tmp_path / "data.json"
        dataset.write_text(json.dumps(data))

        connector = self._make_connector()
        with patch("app.connectors.loopnet_seed.settings") as s:
            s.dataset_path = str(dataset)
            with patch("app.connectors.loopnet_seed.execute_db_safe", new_callable=AsyncMock):
                report = await connector.run()

        assert isinstance(report, IngestionReport)
        assert report.fetched == 1
        assert report.normalized == 1
        assert report.source == "loopnet-seed"

    @pytest.mark.asyncio
    async def test_run_missing_file_raises(self, tmp_path):
        connector = self._make_connector()
        with patch("app.connectors.loopnet_seed.settings") as s:
            s.dataset_path = str(tmp_path / "nonexistent.json")
            with pytest.raises(FileNotFoundError):
                await connector.run()

    @pytest.mark.asyncio
    async def test_run_invalid_json_structure_raises(self, tmp_path):
        dataset = tmp_path / "data.json"
        dataset.write_text('{"not": "a list"}')
        connector = self._make_connector()
        with patch("app.connectors.loopnet_seed.settings") as s:
            s.dataset_path = str(dataset)
            with pytest.raises(ValueError, match="JSON array"):
                await connector.run()

    @pytest.mark.asyncio
    async def test_run_counts_rejected(self, tmp_path):
        data = [
            {"propertyId": "ok1", "address": "1st St", "city": "Dallas"},
            {"propertyId": "bad1"},  # missing address
        ]
        dataset = tmp_path / "data.json"
        dataset.write_text(json.dumps(data))
        connector = self._make_connector()
        with patch("app.connectors.loopnet_seed.settings") as s:
            s.dataset_path = str(dataset)
            with patch("app.connectors.loopnet_seed.execute_db_safe", new_callable=AsyncMock):
                report = await connector.run()

        assert report.fetched == 2
        assert report.normalized == 1
        assert report.rejected == 1
        assert report.rejected_reasons.get("missing_address") == 1
