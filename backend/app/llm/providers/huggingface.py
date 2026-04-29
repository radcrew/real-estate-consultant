"""Hugging Face chat-completions provider client."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import Settings, settings
from app.llm.providers.http_client import post_json

HF_CONNECT_TIMEOUT = 20.0
HF_READ_TIMEOUT = 75.0
HF_WRITE_TIMEOUT = 30.0
HF_POOL_TIMEOUT = 10.0
HF_TRANSIENT_RETRIES = 3
HF_RETRY_BASE_DELAY = 0.35


class HuggingFaceProvider:
    """Provider client for Hugging Face chat-completions requests."""

    def __init__(
        self,
        *,
        settings: Settings,
        timeout: httpx.Timeout | None = None,
        transient_retries: int = HF_TRANSIENT_RETRIES,
        retry_base_delay_s: float = HF_RETRY_BASE_DELAY,
    ) -> None:
        self.settings = settings
        self.timeout = timeout or httpx.Timeout(
            connect = HF_CONNECT_TIMEOUT,
            read = HF_READ_TIMEOUT,
            write = HF_WRITE_TIMEOUT,
            pool = HF_POOL_TIMEOUT,
        )
        self.transient_retries = transient_retries
        self.retry_base_delay_s = retry_base_delay_s

    async def generate_structured_output(
        self,
        *,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Create a Hugging Face chat completion and parse the JSON content it returns."""
        if not self.settings.huggingface_api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Hugging Face API key is not configured.",
            )
        
        payload = {
            "model": self.settings.huggingface_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        headers = {
            "Authorization": f"Bearer {self.settings.huggingface_api_key}",
            "Content-Type": "application/json",
        }
        
        response = await post_json(
            url=self.settings.huggingface_base_url,
            headers=headers,
            payload=payload,
            timeout=self.timeout,
            retries=self.transient_retries,
            retry_base_delay_s=self.retry_base_delay_s,
            error_prefix="Failed to call Hugging Face API",
        )
        
        response_body = response.json()
        response_text = self._extract_chat_completion_text(response_body)
        return self._parse_response_json(response_text)

    def _parse_response_json(self, response_text: str) -> dict[str, Any]:
        try:
            return self._parse_json_object_from_text(response_text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Hugging Face response was not valid JSON.",
            ) from exc

    @staticmethod
    def _parse_json_object_from_text(raw_content: str) -> dict[str, Any]:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response did not contain a JSON object.")
        return json.loads(raw_content[start : end + 1])

    @staticmethod
    def _extract_chat_completion_text(response_body: dict[str, Any]) -> str:
        content = response_body.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            )
        if not isinstance(content, str):
            content = str(content)
        return content


huggingface_provider = HuggingFaceProvider(settings=settings)


__all__ = [
    "huggingface_provider",
]
