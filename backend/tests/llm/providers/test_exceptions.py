import httpx
import pytest
from anthropic import APIStatusError
from anthropic import APITimeoutError as AnthropicAPITimeoutError
from botocore.exceptions import ClientError, ReadTimeoutError
from fastapi import HTTPException
from openai import APITimeoutError, OpenAIError
from pydantic import ValidationError

from app.llm.providers.exceptions import (
    raise_ai_unavailable,
    raise_bedrock_access_denied,
    raise_bedrock_api_error,
    raise_bedrock_completion_parse_failed,
    raise_bedrock_not_configured,
    raise_bedrock_rate_limited,
    raise_bedrock_request_timeout,
    raise_bedrock_structured_refusal,
    raise_bedrock_structured_reply_incomplete,
    raise_embeddings_unavailable,
    raise_hf_api_key_not_configured,
    raise_hf_completion_parse_failed,
    raise_hf_openai_error,
    raise_hf_request_timeout,
    raise_hf_structured_refusal,
    raise_hf_structured_reply_incomplete,
    raise_openrouter_api_key_not_configured,
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
    def test_ai_unavailable_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_ai_unavailable()
        assert info.value.status_code == 503
        assert info.value.detail == "AI unavailable"

    def test_embeddings_unavailable_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_embeddings_unavailable()
        assert info.value.status_code == 503
        assert info.value.detail == "Embeddings unavailable"

    def test_api_key_not_configured_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_hf_api_key_not_configured()
        assert info.value.status_code == 503

    def test_openrouter_api_key_not_configured_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_openrouter_api_key_not_configured()
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


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "InvokeModel")


class TestBedrockProviderExceptions:
    def test_not_configured_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_not_configured()
        assert info.value.status_code == 503
        assert info.value.detail == "AWS region is not configured."

    def test_access_denied_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_access_denied(cause=_client_error("AccessDeniedException"))
        assert info.value.status_code == 503

    def test_rate_limited_raises_503(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_rate_limited(cause=_client_error("ThrottlingException"))
        assert info.value.status_code == 503

    def test_request_timeout_from_anthropic_raises_504(self):
        cause = AnthropicAPITimeoutError(request=httpx.Request("POST", "https://bedrock.example"))
        with pytest.raises(HTTPException) as info:
            raise_bedrock_request_timeout(cause=cause)
        assert info.value.status_code == 504

    def test_request_timeout_from_botocore_raises_504(self):
        """Both SDKs funnel into one raiser, so embeddings timeouts land here too."""
        with pytest.raises(HTTPException) as info:
            raise_bedrock_request_timeout(cause=ReadTimeoutError(endpoint_url="https://bedrock"))
        assert info.value.status_code == 504

    def test_api_error_raises_502(self):
        cause = APIStatusError(
            "upstream fail",
            response=httpx.Response(500, request=httpx.Request("POST", "https://bedrock.example")),
            body=None,
        )
        with pytest.raises(HTTPException) as info:
            raise_bedrock_api_error(cause=cause)
        assert info.value.status_code == 502

    def test_completion_parse_failed_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_completion_parse_failed(cause=_make_validation_error())
        assert info.value.status_code == 502

    def test_structured_refusal_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_structured_refusal(refusal="I cannot help")
        assert info.value.status_code == 502

    def test_structured_reply_incomplete_raises_502(self):
        with pytest.raises(HTTPException) as info:
            raise_bedrock_structured_reply_incomplete()
        assert info.value.status_code == 502

    def test_user_facing_copy_does_not_vary_by_provider(self):
        """Callers must not be able to tell which backend served the request."""
        pairs = [
            (raise_hf_structured_reply_incomplete, raise_bedrock_structured_reply_incomplete),
            (
                lambda: raise_hf_structured_refusal(refusal="no"),
                lambda: raise_bedrock_structured_refusal(refusal="no"),
            ),
        ]
        for hf_raiser, bedrock_raiser in pairs:
            with pytest.raises(HTTPException) as hf_info:
                hf_raiser()
            with pytest.raises(HTTPException) as bedrock_info:
                bedrock_raiser()
            assert hf_info.value.detail == bedrock_info.value.detail
