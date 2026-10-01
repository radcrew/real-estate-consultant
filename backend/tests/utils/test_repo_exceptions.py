import pytest
from fastapi import HTTPException

from app.repositories.exceptions import (
    raise_admin_auth_api_error,
    raise_could_not_load_profile,
    raise_current_password_incorrect,
    raise_intake_questions_load_empty,
    raise_intake_session_not_found,
    raise_profile_service_unavailable,
)
from supabase import AuthApiError


class TestAdminAuthApiError:
    def test_email_exists_raises_409(self):
        exc = AuthApiError("exists", status=400, code="email_exists")
        with pytest.raises(HTTPException) as info:
            raise_admin_auth_api_error(exc)
        assert info.value.status_code == 409

    def test_user_already_exists_raises_409(self):
        exc = AuthApiError("dup", status=400, code="user_already_exists")
        with pytest.raises(HTTPException) as info:
            raise_admin_auth_api_error(exc)
        assert info.value.status_code == 409

    def test_email_not_confirmed_raises_403(self):
        exc = AuthApiError("unconfirmed", status=400, code="email_not_confirmed")
        with pytest.raises(HTTPException) as info:
            raise_admin_auth_api_error(exc)
        assert info.value.status_code == 403

    def test_generic_error_uses_exc_status(self):
        exc = AuthApiError("bad request", status=422, code=None)
        with pytest.raises(HTTPException) as info:
            raise_admin_auth_api_error(exc)
        assert info.value.status_code == 422

    def test_out_of_range_status_falls_back_to_400(self):
        exc = AuthApiError("odd", status=999, code=None)
        with pytest.raises(HTTPException) as info:
            raise_admin_auth_api_error(exc)
        assert info.value.status_code == 400


class TestServiceHelpers:
    def test_could_not_load_profile_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_could_not_load_profile()
        assert info.value.status_code == 503

    def test_profile_service_unavailable_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_profile_service_unavailable()
        assert info.value.status_code == 503

    def test_current_password_incorrect_raises_401(self):
        with pytest.raises(HTTPException) as info:
            raise_current_password_incorrect()
        assert info.value.status_code == 401

    def test_intake_session_not_found_raises_404(self):
        with pytest.raises(HTTPException) as info:
            raise_intake_session_not_found()
        assert info.value.status_code == 404

    def test_intake_questions_load_empty_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_intake_questions_load_empty()
        assert info.value.status_code == 502
