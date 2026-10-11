import pytest
from fastapi import HTTPException

from app.repositories.exceptions import (
    raise_current_password_incorrect,
    raise_intake_questions_load_empty,
    raise_intake_session_not_found,
)


class TestServiceHelpers:
    def test_current_password_incorrect_raises_400(self):
        with pytest.raises(HTTPException) as info:
            raise_current_password_incorrect()
        assert info.value.status_code == 400

    def test_intake_session_not_found_raises_404(self):
        with pytest.raises(HTTPException) as info:
            raise_intake_session_not_found()
        assert info.value.status_code == 404

    def test_intake_questions_load_empty_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_intake_questions_load_empty()
        assert info.value.status_code == 502
