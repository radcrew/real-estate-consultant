import logging

from app.logging import configure_logging


def test_configure_logging_quiets_mcp_sdk() -> None:
    configure_logging("INFO")
    assert logging.getLogger("mcp.server.lowlevel.server").level == logging.WARNING
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger().level == logging.INFO
