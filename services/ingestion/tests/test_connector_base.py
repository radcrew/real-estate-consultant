"""Tests for ConnectorBase and IngestionReport."""
import pytest
from unittest.mock import MagicMock

from app.connectors.base import ConnectorBase, IngestionReport


class TestIngestionReport:
    def test_rejected_is_fetched_minus_normalized(self):
        report = IngestionReport(source="test", fetched=10, normalized=7)
        assert report.rejected == 3

    def test_rejected_zero_when_all_normalized(self):
        report = IngestionReport(source="test", fetched=5, normalized=5)
        assert report.rejected == 0

    def test_rejected_reasons_defaults_to_empty(self):
        report = IngestionReport(source="test", fetched=3, normalized=3)
        assert report.rejected_reasons == {}

    def test_custom_rejected_reasons(self):
        report = IngestionReport(
            source="loopnet-seed",
            fetched=20,
            normalized=15,
            rejected_reasons={"missing_address": 3, "invalid_type": 2},
        )
        assert report.rejected_reasons["missing_address"] == 3
        assert report.rejected == 5


class TestConnectorBase:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            ConnectorBase(client=MagicMock())

    def test_concrete_subclass_works(self):
        class FakeConnector(ConnectorBase):
            @property
            def name(self) -> str:
                return "fake"

            async def run(self) -> IngestionReport:
                return IngestionReport(source=self.name, fetched=0, normalized=0)

        connector = FakeConnector(client=MagicMock())
        assert connector.name == "fake"

    def test_client_stored_on_instance(self):
        class FakeConnector(ConnectorBase):
            @property
            def name(self):
                return "fake"

            async def run(self):
                return IngestionReport(source="fake", fetched=0, normalized=0)

        mock_client = MagicMock()
        connector = FakeConnector(client=mock_client)
        assert connector._client is mock_client
