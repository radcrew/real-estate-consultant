"""Hugging Face-backed intake prompt parsing and follow-up generation."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.llm.intake_parse_schema import (
    format_intake_parse_schema_for_prompt,
    question_criteria_keys,
    required_criteria_keys_for_llm,
)
from app.schemas.llm_intake_parse import LlmParseModelOutput

# Separate connect vs read: slow inference should not share the same budget as TLS setup.
_HF_HTTP_TIMEOUT = httpx.Timeout(connect=20.0, read=75.0, write=30.0, pool=10.0)
_HF_TRANSIENT_RETRIES = 3
_HF_RETRY_BASE_DELAY_S = 0.35


async def _post_huggingface_chat(
    *,
    payload: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    """POST to Hugging Face with retries for transient connection failures."""
    last_exc: httpx.HTTPError | None = None
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
            last_exc = exc
            if attempt + 1 < _HF_TRANSIENT_RETRIES:
                await asyncio.sleep(_HF_RETRY_BASE_DELAY_S * (2**attempt))
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to call Hugging Face API: {exc}",
            ) from exc

    assert last_exc is not None
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Failed to call Hugging Face API after retries: {last_exc}",
    ) from last_exc


def _extract_json_payload(raw_content: str) -> dict[str, Any]:
    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain JSON object.")
    return json.loads(raw_content[start : end + 1])


def _fallback_missing_fields(
    merged_criteria: dict[str, Any],
    required_fields: list[str],
) -> list[str]:
    return [key for key in required_fields if key not in merged_criteria]


async def extract_intake_from_input(
    *,
    user_input: str,
    existing_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Use Hugging Face chat completion API to extract criteria and suggest next question."""
    if not settings.huggingface_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face API key is not configured.",
        )

    question_keys = question_criteria_keys(questions)
    required_fields = required_criteria_keys_for_llm(questions)
    schema_block = format_intake_parse_schema_for_prompt(questions=questions)

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
            "existing_criteria": existing_criteria,
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

    response = await _post_huggingface_chat(payload=payload, headers=headers)

    body = response.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )
    if not isinstance(content, str):
        content = str(content)

    try:
        parsed = _extract_json_payload(content)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response was not valid JSON.",
        ) from exc

    try:
        normalized = LlmParseModelOutput.model_validate(
            parsed,
            context={"allowed_criteria_keys": question_keys},
        )
    except ValidationError:
        extracted = parsed.get("extracted")
        if not isinstance(extracted, dict):
            extracted = {}
        extracted = {k: v for k, v in extracted.items() if k in set(question_keys)}
        merged_criteria = {**existing_criteria, **extracted}
        missing_fields = parsed.get("missing_fields")
        if not isinstance(missing_fields, list):
            missing_fields = _fallback_missing_fields(merged_criteria, required_fields)
        else:
            missing_fields = [
                k for k in missing_fields if isinstance(k, str) and k in required_fields
            ]
        next_question = parsed.get("next_question")
        if not isinstance(next_question, dict):
            next_question = {"key": None, "text": None}
        is_complete = parsed.get("is_complete")
        if not isinstance(is_complete, bool):
            is_complete = len(missing_fields) == 0
        return {
            "extracted": extracted,
            "merged_criteria": merged_criteria,
            "missing_fields": missing_fields,
            "next_question": next_question,
            "is_complete": is_complete,
        }

    extracted = normalized.extracted
    merged_criteria = {**existing_criteria, **extracted}
    still_needed = _fallback_missing_fields(merged_criteria, required_fields)
    model_missing = [k for k in normalized.missing_fields if k in required_fields]
    if model_missing:
        missing_fields = [k for k in model_missing if k in still_needed]
        if not missing_fields:
            missing_fields = still_needed
    else:
        missing_fields = still_needed

    next_question = normalized.next_question.model_dump()
    is_complete = len(missing_fields) == 0

    return {
        "extracted": extracted,
        "merged_criteria": merged_criteria,
        "missing_fields": missing_fields,
        "next_question": next_question,
        "is_complete": is_complete,
    }


async def generate_llm_opening_question_text(
    *,
    welcome_message: str,
    question_key: str,
    question_type: str,
    question_options: Any | None = None,
) -> str:
    """Ask the model for a single conversational question line (JSON ``{"text": "..."}``)."""
    if not settings.huggingface_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face API key is not configured.",
        )

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
    user_prompt = json.dumps(user_payload, ensure_ascii=True)

    payload = {
        "model": settings.huggingface_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 200,
    }
    headers = {
        "Authorization": f"Bearer {settings.huggingface_api_key}",
        "Content-Type": "application/json",
    }

    response = await _post_huggingface_chat(payload=payload, headers=headers)

    body = response.json()
    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if isinstance(content, list):
        content = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict)
        )
    if not isinstance(content, str):
        content = str(content)

    try:
        parsed = _extract_json_payload(content)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response was not valid JSON.",
        ) from exc

    text = parsed.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response missing text field.",
        )
    return text.strip()
