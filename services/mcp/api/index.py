"""Vercel serverless entrypoint (see ``vercel.json``)."""

from app.config import settings
from app.logging import configure_logging

configure_logging(settings.log_level)

from app.asgi import app  # noqa: E402, F401
