"""Tests for app.core.auth — internal bearer token validation."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.core.auth import require_internal_token


def _request(token: str = "") -> MagicMock:
    req = MagicMock()
    req.headers = {"authorization": f"Bearer {token}" if token else ""}
    return req


class TestRequireInternalToken:
    def test_valid_trigger_token_passes(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = "secret"
            s.service_auth_token = ""
            s.service_auth_token_next = ""
            require_internal_token(_request("secret"))  # no exception

    def test_valid_service_token_passes(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = ""
            s.service_auth_token = "svc-token"
            s.service_auth_token_next = ""
            require_internal_token(_request("svc-token"))

    def test_valid_next_token_passes(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = ""
            s.service_auth_token = "old"
            s.service_auth_token_next = "new"
            require_internal_token(_request("new"))

    def test_wrong_token_raises_401(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = "correct"
            s.service_auth_token = ""
            s.service_auth_token_next = ""
            with pytest.raises(HTTPException) as info:
                require_internal_token(_request("wrong"))
            assert info.value.status_code == 401

    def test_no_tokens_configured_raises_503(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = ""
            s.service_auth_token = ""
            s.service_auth_token_next = ""
            with pytest.raises(HTTPException) as info:
                require_internal_token(_request("anything"))
            assert info.value.status_code == 503

    def test_missing_authorization_header_raises_401(self):
        with patch("app.core.auth.settings") as s:
            s.trigger_token = "secret"
            s.service_auth_token = ""
            s.service_auth_token_next = ""
            with pytest.raises(HTTPException) as info:
                require_internal_token(_request(""))
            assert info.value.status_code == 401

    def test_non_bearer_scheme_raises_401(self):
        req = MagicMock()
        req.headers = {"authorization": "Basic secret"}
        with patch("app.core.auth.settings") as s:
            s.trigger_token = "secret"
            s.service_auth_token = ""
            s.service_auth_token_next = ""
            with pytest.raises(HTTPException) as info:
                require_internal_token(req)
            assert info.value.status_code == 401
