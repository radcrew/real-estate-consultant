"""Intake orchestration: LLM provider calls and next-question resolution."""

from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from pydantic import ValidationError

from app.llm.intake.schema import extract_question_keys, render_intake_response_schema
from app.llm.providers import huggingface_provider
from app.llm.providers.prompts import (
    DEFAULT_NEXT_QUESTION_PLACEHOLDER,
    INTAKE_PARSE_SYSTEM_PROMPT_HEADER,
    INTAKE_PARSE_SYSTEM_PROMPT_RULES,
    OPENING_QUESTION_OPTIONS_HINT,
    OPENING_QUESTION_SYSTEM_PROMPT_BASE,
)
from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.schemas.llm_intake_parse import LlmParseModelOutput
from app.utils.intake_validation import merge_missing_fields

QuestionRow = dict[str, Any]


async def parse_user_input(
    *,
    user_input: str,
    current_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Parse free-form user intake input into structured criteria and next-step hints."""
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
    parsed_payload = await huggingface_provider.generate_structured_output(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=450,
    )
    return _build_intake_parse_result(
        parsed_payload=parsed_payload,
        question_keys=question_keys,
        current_criteria=current_criteria,
        required_fields=required_fields,
    )


async def generate_opening_question(
    *,
    welcome_message: str,
    question_key: str,
    question_type: str,
    question_options: Any | None = None,
) -> str:
    """Generate the opening intake question text via the configured provider."""
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

    response_body = await huggingface_provider.generate_structured_output(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        temperature=0.35,
        max_tokens=200,
    )
    text = response_body.get("text")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face response missing text field.",
        )
    return text.strip()


def find_question_row_by_key(
    questions: list[QuestionRow],
    question_key: str,
) -> QuestionRow | None:
    return next((row for row in questions if row.get("key") == question_key), None)


def resolve_next_intake_question(
    questions: list[QuestionRow],
    suggested_question: object,
    missing_fields: list[str],
) -> IntakeSessionFirstQuestion | None:
    """Prefer LLM-authored text while anchoring the result to a known question row."""
    if not isinstance(suggested_question, dict):
        suggested_question = {}

    suggested_key = suggested_question.get("key")
    suggested_text = suggested_question.get("text")

    if isinstance(suggested_text, str) and suggested_text.strip():
        question_text = suggested_text.strip()
        matched_row = (
            find_question_row_by_key(questions, suggested_key)
            if isinstance(suggested_key, str)
            else None
        )
        if matched_row is None and missing_fields:
            matched_row = find_question_row_by_key(questions, missing_fields[0])
        if matched_row is not None:
            mapped = map_question_to_model(matched_row)
            return IntakeSessionFirstQuestion(
                key=mapped.key,
                text=question_text,
                type=mapped.type,
                options=mapped.options,
            )
        return IntakeSessionFirstQuestion(
            key="llm_followup",
            text=question_text,
            type="text",
            options=None,
        )

    if isinstance(suggested_key, str):
        matched_row = find_question_row_by_key(questions, suggested_key)
        if matched_row is not None:
            return map_question_to_model(matched_row)

    for row in questions:
        row_key = row.get("key")
        if isinstance(row_key, str) and row_key in missing_fields:
            return map_question_to_model(row)
    return None


def _build_intake_parse_result(
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
        return _build_intake_parse_fallback(
            parsed_payload=parsed_payload,
            current_criteria=current_criteria,
            question_keys=question_keys,
            required_fields=required_fields,
        )

    extracted = normalized_output.extracted
    merged_criteria = {**current_criteria, **extracted}
    missing_fields = merge_missing_fields(
        merged_criteria=merged_criteria,
        required_fields=required_fields,
        model_missing=normalized_output.missing_fields,
    )

    next_question = normalized_output.next_question.model_dump()
    is_complete = len(missing_fields) == 0

    return {
        "extracted": extracted,
        "merged_criteria": merged_criteria,
        "missing_fields": missing_fields,
        "next_question": next_question,
        "is_complete": is_complete,
    }


def _build_intake_parse_fallback(
    *,
    parsed_payload: dict[str, Any],
    current_criteria: dict[str, Any],
    question_keys: list[str],
    required_fields: list[str],
) -> dict[str, Any]:
    raw_extracted = parsed_payload.get("extracted")
    if isinstance(raw_extracted, dict):
        allowed_keys = set(question_keys)
        extracted = {
            key: value for key, value in raw_extracted.items() if key in allowed_keys
        }
    else:
        extracted = {}

    merged_criteria = {**current_criteria, **extracted}

    raw_missing_fields = parsed_payload.get("missing_fields")
    if isinstance(raw_missing_fields, list):
        missing_fields = [
            key
            for key in raw_missing_fields
            if isinstance(key, str) and key in required_fields
        ]
    else:
        missing_fields = [key for key in required_fields if key not in merged_criteria]

    raw_next_question = parsed_payload.get("next_question")
    next_question = (
        raw_next_question
        if isinstance(raw_next_question, dict)
        else dict(DEFAULT_NEXT_QUESTION_PLACEHOLDER)
    )

    raw_is_complete = parsed_payload.get("is_complete")
    is_complete = (
        raw_is_complete
        if isinstance(raw_is_complete, bool)
        else len(missing_fields) == 0
    )

    return {
        "extracted": extracted,
        "merged_criteria": merged_criteria,
        "missing_fields": missing_fields,
        "next_question": next_question,
        "is_complete": is_complete,
    }
