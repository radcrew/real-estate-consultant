"""Client-side errors — re-exported from ``app.auth`` for compatibility."""

from __future__ import annotations

from app.auth.errors import AuthInvalidError, AuthRequiredError

__all__ = ["AuthInvalidError", "AuthRequiredError"]
