"""Hugging Face-backed intake parsing and opening-question generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.llm.intake.schema import (
    list_available_question_keys,
    list_required_question_keys,
    render_intake_response_schema,
)
from app.schemas.llm_intake_parse import LlmParseModelOutput

_HF_HTTP_TIMEOUT = httpx.Timeout(connect=20.0, read=75.0, write=30.0, pool=10.0)
_HF_TRANSIENT_RETRIES = 3
_HF_RETRY_BASE_DELAY_S = 0.35


async def _call_huggingface_chat_completion(
    *,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    """POST to Hugging Face with retries for transient connection failures."""
    last_exception: httpx.HTTPError | None = None
    for attempt in range(_HF_TRANSIENT_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=_HF_HTTP_TIMEOUT) as client:
                response = await client.post(
                    settings.huggingface_base_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            last_exception = exc
            if attempt + 1 < _HF_TRANSIENT_RETRIES:
                await asyncio.sleep(_HF_RETRY_BASE_DELAY_S * (2**attempt))
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to call Hugging Face API: {exc}",
            ) from exc

    assert last_exception is not None
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Failed to call Hugging Face API after retries: {last_exception}",
    ) from last_exception


def _parse_json_object_from_text(raw_content: str) -> dict[str, Any]:
    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(raw_content[start : end + 1])


def _missing_required_fields(
    merged_criteria: dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    return [key for key in required_fields if key not in merged_criteria]


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


def _ensure_huggingface_api_key() -> None:
    if settings.huggingface_api_key.strip():
        return
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Hugging Face API key is not configured.",
    )


async def extract_intake_with_huggingface(
    *,
    user_input: str,
    validated_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract intake criteria and suggest a follow-up question from free-form text."""
    _ensure_huggingface_api_key()

    question_keys = list_available_question_keys(questions)
    required_fields = list_required_question_keys(questions)
    schema_block = render_intake_response_schema(questions=questions)

    system_prompt = (
        "You parse user real-estate search prompts into structured JSON.\n"
        "Return ONLY one JSON object that validates against this JSON Schema "
        "(no markdown fences, no commentary):\n"
        f"{schema_block}\n"
        "Rules:\n"
        "- Keep ``extracted`` sparse: omit properties when unknown.\n"
        "- ``missing_fields`` must list only keys still missing from required criteria "
        "(see required_fields in the user message).\n"
        "- ``next_question.key`` should be one of question_keys when possible, "
        "ideally the first missing required field.\n"
        "- ``next_question.text`` should be concise and conversational."
    )

    user_prompt = json.dumps(
        {
            "user_input": user_input,
            "validated_criteria": validated_criteria,
            "question_keys": question_keys,
            "required_fields": required_fields,
        },
        ensure_ascii=True,
    )

    payload = {
        "model": settings.huggingface_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 450,
    }
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }

    response = await _call_huggingface_chat_completion(payload=payload, headers=headers)
    response_body = response.json()
    response_text = _extract_chat_message_text(response_body)

    try:
        parsed_payload = _parse_json_object_from_text(response_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response was not valid JSON.",
        ) from exc

    try:
        normalized_output = LlmParseModelOutput.model_validate(
            parsed_payload,
            context={"allowed_criteria_keys": question_keys},
        )
    except ValidationError:
        extracted = parsed_payload.get("extracted")
        if not isinstance(extracted, dict):
            extracted = {}
        extracted = {key: value for key, value in extracted.items() if key in set(question_keys)}
        merged_criteria = {**validated_criteria, **extracted}

        missing_fields = parsed_payload.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = _missing_required_fields(merged_criteria, required_fields)
        else:
            missing_fields = [
                key for key in missing_fields if isinstance(key, str) and key in required_fields
            ]

        next_question = parsed_payload.get("next_question")
        if not isinstance(next_question, dict):
            next_question = {"key": None, "text": None}

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

    extracted = normalized_output.extracted
    merged_criteria = {**validated_criteria, **extracted}
    still_missing = _missing_required_fields(merged_criteria, required_fields)
    model_missing = [key for key in normalized_output.missing_fields if key in required_fields]

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


async def generate_opening_question_with_huggingface(
    *,
    welcome_message: str,
    question_key: str,
    question_type: str,
    question_options: Any | None = None,
) -> str:
    """Generate one short conversational opening question line as JSON."""
    _ensure_huggingface_api_key()

    system_prompt = (
        "You write one short, friendly question for a commercial real-estate intake chatbot.\n"
        "Return ONLY valid JSON: {\"text\": string}\n"
        "The question should invite the user to describe what they are looking for in "
        "natural language.\n"
        "Do not repeat the entire welcome message; write only the question line "
        "(one or two sentences max)."
    )
    if question_options is not None:
        system_prompt += (
            "\nIf question_options lists choices, phrase the question so the user can select "
            "from those options (you may name the options briefly) or add a short clarification."
        )

    user_payload: dict[str, Any] = {
        "welcome_message": welcome_message,
        "question_key": question_key,
        "question_type": question_type,
    }
    if question_options is not None:
        user_payload["question_options"] = question_options

    payload = {
        "model": settings.huggingface_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        "temperature": 0.35,
        "max_tokens": 200,
    }
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }

    response = await _call_huggingface_chat_completion(payload=payload, headers=headers)
    response_body = response.json()
    response_text = _extract_chat_message_text(response_body)

    try:
        parsed_payload = _parse_json_object_from_text(response_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response was not valid JSON.",
        ) from exc

    text = parsed_payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response missing text field.",
        )
    return text.strip()


