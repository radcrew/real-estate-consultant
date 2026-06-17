import pytest
from fastapi import HTTPException
from openai import APITimeoutError, OpenAIError
from pydantic import ValidationError

from app.llm.providers.exceptions import (
    raise_hf_api_key_not_configured,
    raise_hf_completion_parse_failed,
    raise_hf_openai_error,
    raise_hf_request_timeout,
    raise_hf_structured_refusal,
    raise_hf_structured_reply_incomplete,
)


def _make_validation_error():
    from pydantic import BaseModel
    class M(BaseModel):
        x: int
    try:
        M(x="bad")
    except ValidationError as e:
        return e


class TestLlmProviderExceptions:
    def test_api_key_not_configured_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_api_key_not_configured()
        assert info.value.status_code == 503

    def test_completion_parse_failed_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_completion_parse_failed(cause=_make_validation_error())
        assert info.value.status_code == 502

    def test_request_timeout_raises_504(self):
        import httpx
        cause = APITimeoutError(request=httpx.Request("POST", "https://api.example.com"))
        with pytest.raises(HTTPException) as info:
            raise_hf_request_timeout(cause=cause)
        assert info.value.status_code == 504

    def test_openai_error_raises_502(self):
        cause = OpenAIError("upstream fail")
        with pytest.raises(HTTPException) as info:
            raise_hf_openai_error(cause=cause)
        assert info.value.status_code == 502

    def test_structured_refusal_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_structured_refusal(refusal="I cannot help")
        assert info.value.status_code == 502

    def test_structured_reply_incomplete_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_structured_reply_incomplete()
        assert info.value.status_code == 502
