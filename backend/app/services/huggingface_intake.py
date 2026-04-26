"""Hugging Face-backed intake prompt parsing and follow-up generation."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import settings

_TIMEOUT_SECONDS = 25.0


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


async def parse_intake_with_huggingface(
    *,
    user_input: str,
    existing_criteria: dict[str, Any],
    question_keys: list[str],
    required_fields: list[str],
) -> dict[str, Any]:
    """Use Hugging Face chat completion API to extract criteria and suggest next question."""
    if not settings.huggingface_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face API key is not configured.",
        )

    system_prompt = (
        "You parse user real-estate search prompts into structured JSON.\n"
        "Return ONLY valid JSON with this shape:\n"
        "{\n"
        '  "extracted": {\n'
        '    "building_type": [string],\n'
        '    "location": {"label": string, "lat": number|null, "lng": number|null},\n'
        '    "size_sqft": {"min": number|null, "max": number|null},\n'
        '    "rent_range": {"min": number|null, "max": number|null}\n'
        "  },\n"
        '  "missing_fields": [string],\n'
        '  "next_question": {"key": string|null, "text": string|null},\n'
        '  "is_complete": boolean\n'
        "}\n"
        "Rules:\n"
        "- Use null for unknown nested values.\n"
        "- Keep extracted object sparse: omit fields if unknown.\n"
        "- missing_fields should include only fields from required_fields.\n"
        "- next_question.key should be one of question_keys and ideally in missing_fields.\n"
        "- next_question.text should be concise and conversational."
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

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                settings.huggingface_base_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to call Hugging Face API: {exc}",
        ) from exc

    body = response.json()
    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
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

    extracted = parsed.get("extracted")
    if not isinstance(extracted, dict):
        extracted = {}

    merged_criteria = {**existing_criteria, **extracted}
    missing_fields = parsed.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = _fallback_missing_fields(merged_criteria, required_fields)
    else:
        missing_fields = [k for k in missing_fields if isinstance(k, str) and k in required_fields]

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


async def generate_llm_opening_question_text(
    *,
    welcome_message: str,
    question_key: str,
    question_type: str,
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
        "The question should invite the user to describe what they are looking for in natural language.\n"
        "Do not repeat the entire welcome message; write only the question line (one or two sentences max)."
    )
    user_prompt = json.dumps(
        {
            "welcome_message": welcome_message,
            "question_key": question_key,
            "question_type": question_type,
        },
        ensure_ascii=True,
    )

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

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                settings.huggingface_base_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to call Hugging Face API: {exc}",
        ) from exc

    body = response.json()
    content = (
        body.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
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
