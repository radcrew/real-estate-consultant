import pytest
from fastapi import HTTPException

from app.llm.outreach.exceptions import raise_outreach_email_empty


class TestLlmOutreachExceptions:
    def test_outreach_email_empty_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_outreach_email_empty()
        assert info.value.status_code == 502
