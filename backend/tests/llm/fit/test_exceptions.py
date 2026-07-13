import pytest
from fastapi import HTTPException

from app.llm.fit.exceptions import raise_fit_explanation_empty


class TestLlmFitExceptions:
    def test_fit_explanation_empty_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_fit_explanation_empty()
        assert info.value.status_code == 502
