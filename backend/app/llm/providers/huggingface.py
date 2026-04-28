"""Hugging Face-backed intake parsing and opening-question generation."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.llm.intake.schema import extract_question_keys, render_intake_response_schema
from app.llm.providers.http_client import post_json
from app.llm.providers.prompts import (
    DEFAULT_NEXT_QUESTION_PLACEHOLDER,
    INTAKE_PARSE_SYSTEM_PROMPT_HEADER,
    INTAKE_PARSE_SYSTEM_PROMPT_RULES,
    OPENING_QUESTION_OPTIONS_HINT,
    OPENING_QUESTION_SYSTEM_PROMPT_BASE,
)
from app.schemas.llm_intake_parse import LlmParseModelOutput

HF_CONNECT_TIMEOUT = 20.0
HF_READ_TIMEOUT = 75.0
HF_WRITE_TIMEOUT = 30.0
HF_POOL_TIMEOUT = 10.0
HF_TRANSIENT_RETRIES = 3
HF_RETRY_BASE_DELAY = 0.35


class HuggingFaceProvider:
    """Provider client for Hugging Face chat-completions based LLM tasks."""

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

    async def parse_user_input(
        self,
        *,
        user_input: str,
        current_criteria: dict[str, Any],
        questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract intake criteria and suggest a follow-up question from free-form text."""
        self._require_api_key()

        question_keys, required_fields = extract_question_keys(questions)
        intake_schema = render_intake_response_schema(questions=questions)
        system_prompt = (
            f"{INTAKE_PARSE_SYSTEM_PROMPT_HEADER}{intake_schema}\n"
            f"{INTAKE_PARSE_SYSTEM_PROMPT_RULES}"
        )

        user_prompt = json.dumps(
            {
                "user_input": user_input,
                "current_criteria": current_criteria,
                "question_keys": question_keys,
                "required_fields": required_fields,
            },
            ensure_ascii=True,
        )

        response_body = await self._post_messages(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=450,
        )
        response_text = self._extract_chat_message_text(response_body)
        parsed_payload = self._parse_llm_response_json(response_text)
        return self._compose_intake_parse_result(
            parsed_payload=parsed_payload,
            question_keys=question_keys,
            current_criteria=current_criteria,
            required_fields=required_fields,
        )

    async def generate_opening_question_text(
        self,
        *,
        welcome_message: str,
        question_key: str,
        question_type: str,
        question_options: Any | None = None,
    ) -> str:
        """Generate one short conversational opening question line as JSON."""
        self._require_api_key()

        system_prompt = OPENING_QUESTION_SYSTEM_PROMPT_BASE
        if question_options is not None:
            system_prompt += OPENING_QUESTION_OPTIONS_HINT

        user_payload: dict[str, Any] = {
            "welcome_message": welcome_message,
            "question_key": question_key,
            "question_type": question_type,
        }
        if question_options is not None:
            user_payload["question_options"] = question_options

        response_body = await self._post_messages(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=True),
                },
            ],
            temperature=0.35,
            max_tokens=200,
        )
        response_text = self._extract_chat_message_text(response_body)
        parsed_payload = self._parse_llm_response_json(response_text)

        text = parsed_payload.get("text")
        if not isinstance(text, str) or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Hugging Face response missing text field.",
            )
        return text.strip()

    async def _post_messages(
        self,
        *,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """POST chat messages to the provider and return parsed JSON body."""
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
        return response.json()

    def _build_intake_parse_fallback(
        self,
        *,
        parsed_payload: dict[str, Any],
        current_criteria: dict[str, Any],
        question_keys: list[str],
        required_fields: list[str],
    ) -> dict[str, Any]:
        extracted = parsed_payload.get("extracted")
        if not isinstance(extracted, dict):
            extracted = {}
        allowed_keys = set(question_keys)
        extracted = {key: value for key, value in extracted.items() if key in allowed_keys}
        merged_criteria = {**current_criteria, **extracted}

        missing_fields = parsed_payload.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = self._missing_required_fields(merged_criteria, required_fields)
        else:
            missing_fields = [
                key for key in missing_fields if isinstance(key, str) and key in required_fields
            ]

        next_question = parsed_payload.get("next_question")
        if not isinstance(next_question, dict):
            next_question = dict(DEFAULT_NEXT_QUESTION_PLACEHOLDER)

        is_complete = parsed_payload.get("is_complete")
        if not isinstance(is_complete, bool):
            is_complete = len(missing_fields) == 0

        return {
            "extracted": extracted,
            "merged_criteria": merged_criteria,
            "missing_fields": missing_fields,
            "next_question": next_question,
            "is_complete": is_complete,
        }

    def _compose_intake_parse_result(
        self,
        *,
        parsed_payload: dict[str, Any],
        question_keys: list[str],
        current_criteria: dict[str, Any],
        required_fields: list[str],
    ) -> dict[str, Any]:
        try:
            normalized_output = LlmParseModelOutput.model_validate(
                parsed_payload,
                context={"allowed_criteria_keys": question_keys},
            )
        except ValidationError:
            return self._build_intake_parse_fallback(
                parsed_payload=parsed_payload,
                current_criteria=current_criteria,
                question_keys=question_keys,
                required_fields=required_fields,
            )

        extracted = normalized_output.extracted
        merged_criteria = {**current_criteria, **extracted}
        still_missing = self._missing_required_fields(merged_criteria, required_fields)
        model_missing = [
            key for key in normalized_output.missing_fields if key in required_fields
        ]

        if model_missing:
            missing_fields = [key for key in model_missing if key in still_missing]
            if not missing_fields:
                missing_fields = still_missing
        else:
            missing_fields = still_missing

        next_question = normalized_output.next_question.model_dump()
        is_complete = len(missing_fields) == 0

        return {
            "extracted": extracted,
            "merged_criteria": merged_criteria,
            "missing_fields": missing_fields,
            "next_question": next_question,
            "is_complete": is_complete,
        }

    def _require_api_key(self) -> None:
        if self.settings.huggingface_api_key.strip():
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face API key is not configured.",
        )

    def _parse_llm_response_json(self, response_text: str) -> dict[str, Any]:
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
    def _missing_required_fields(
        merged_criteria: dict[str, Any],
        required_fields: list[str],
    ) -> list[str]:
        return [key for key in required_fields if key not in merged_criteria]

    @staticmethod
    def _extract_chat_message_text(response_body: dict[str, Any]) -> str:
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
