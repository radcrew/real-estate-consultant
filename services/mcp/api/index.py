"""Vercel serverless entrypoint (see ``vercel.json``)."""

from app.asgi import app  # noqa: F401
