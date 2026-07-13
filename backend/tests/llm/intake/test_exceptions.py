import pytest
from fastapi import HTTPException

from app.llm.intake.exceptions import raise_hf_opening_response_missing_text


class TestLlmIntakeExceptions:
    def test_opening_response_missing_text_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_opening_response_missing_text()
        assert info.value.status_code == 502
