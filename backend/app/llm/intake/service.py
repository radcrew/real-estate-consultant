"""Intake orchestration: LLM provider calls and next-question resolution."""

from __future__ import annotations

import json
from typing import Any

from app.domain.intake_next_question import (
    find_question_row_by_key,
    first_question_row_in_missing,
    match_row_for_text_suggestion,
    suggested_question_as_dict,
)
from app.domain.intake_validation import merge_missing_fields
from app.llm.intake.exceptions import raise_hf_opening_response_missing_text
from app.llm.intake.schema import extract_question_keys, render_intake_response_schema
from app.llm.providers.chat import generate_structured_output
from app.llm.providers.prompts import (
    INTAKE_PARSE_SYSTEM_PROMPT_HEADER,
    INTAKE_PARSE_SYSTEM_PROMPT_RULES,
    OPENING_QUESTION_OPTIONS_HINT,
    OPENING_QUESTION_SYSTEM_PROMPT_BASE,
)
from app.llm.providers.routing import LlmTask
from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.schemas.llm_intake_parse import LlmOpeningQuestionOutput, LlmParseModelOutput

QuestionRow = dict[str, Any]

# Reserved criteria key holding required fields the user explicitly declined to answer.
SKIPPED_FIELDS_KEY = "_skipped_fields"


def pending_question_for(
    questions: list[QuestionRow],
    *,
    criteria: dict[str, Any],
    required_fields: list[str],
    skipped: list[str],
) -> dict[str, Any] | None:
    """The question the user is most likely replying to, or ``None`` when none is open.

    Derived rather than stored: the session keeps criteria, not the last question asked,
    and the next question is itself chosen as the first unanswered required field — so
    recomputing it here reaches the same one without new state to keep in step.

    Without this the parser sees a bare "1000" with no idea which field it answers, and
    has to guess from the shape of the number alone.
    """
    key = next(
        (k for k in required_fields if k not in criteria and k not in skipped),
        None,
    )
    if key is None:
        return None
    row = find_question_row_by_key(questions, key)
    if row is None:
        return None
    # Read the two fields directly rather than mapping the whole row: this is prompt
    # context, so a row too incomplete to render as a question should still be able to
    # say which field is open.
    text = row.get("text")
    return {"key": key, "text": text if isinstance(text, str) else ""}


async def parse_user_input(
    *,
    user_input: str,
    current_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Parse free-form user intake input into structured criteria and next-step hints."""
    question_keys, required_fields = extract_question_keys(questions)
    previously_skipped = [
        key for key in current_criteria.get(SKIPPED_FIELDS_KEY, []) if isinstance(key, str)
    ]
    criteria_for_prompt = {k: v for k, v in current_criteria.items() if k != SKIPPED_FIELDS_KEY}
    asked_question = pending_question_for(
        questions,
        criteria=criteria_for_prompt,
        required_fields=required_fields,
        skipped=previously_skipped,
    )

    intake_schema = render_intake_response_schema(questions=questions)
    system_prompt = (
        f"{INTAKE_PARSE_SYSTEM_PROMPT_HEADER}{intake_schema}\n"
        f"{INTAKE_PARSE_SYSTEM_PROMPT_RULES}"
    )
    user_prompt = json.dumps(
        {
            "user_input": user_input,
            "asked_question": asked_question,
            "current_criteria": criteria_for_prompt,
            "question_keys": question_keys,
            "required_fields": required_fields,
            "previously_skipped_fields": previously_skipped,
        },
        ensure_ascii=True,
    )
    parsed_output = await generate_structured_output(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=LlmParseModelOutput,
        temperature=0.1,
        max_tokens=800,
        task=LlmTask.INTAKE_PARSE,
    )
    return _build_intake_parse_result(
        parsed_output=parsed_output,
        question_keys=question_keys,
        current_criteria=criteria_for_prompt,
        required_fields=required_fields,
        previously_skipped=previously_skipped,
    )


async def generate_opening_question(
    *,
    welcome_message: str,
    key: str,
    type: str,
    options: Any | None = None,
) -> str:
    """Generate the opening intake question text via the configured provider."""
    system_prompt = OPENING_QUESTION_SYSTEM_PROMPT_BASE
    if options is not None:
        system_prompt += OPENING_QUESTION_OPTIONS_HINT

    user_payload: dict[str, Any] = {
        "welcome_message": welcome_message,
        "question_key": key,
        "question_type": type,
    }
    if options is not None:
        user_payload["question_options"] = options

    response_output = await generate_structured_output(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=True)},
        ],
        response_format=LlmOpeningQuestionOutput,
        temperature=0.35,
        max_tokens=200,
        task=LlmTask.OPENING_QUESTION,
    )
    text = response_output.text
    if not text:
        raise_hf_opening_response_missing_text()
    return text.strip()


def resolve_next_intake_question(
    questions: list[QuestionRow],
    suggested_question: object,
    missing_fields: list[str],
) -> IntakeSessionFirstQuestion | None:
    """Prefer LLM-authored text while anchoring the result to a known question row."""
    # Nothing missing means nothing left to ask, whatever the model suggested. It goes on
    # proposing the field it just collected — the intake is complete but the suggestion
    # still names ``size_sqft`` — and the client shows any question it is handed, so the
    # user answers the same one forever and never reaches the end. This is the same
    # condition the caller reports as ``is_complete``.
    if not missing_fields:
        return None

    suggested = suggested_question_as_dict(suggested_question)
    suggested_key = suggested.get("key")
    suggested_text = suggested.get("text")

    # Handle text suggestion
    if isinstance(suggested_text, str) and (text := suggested_text.strip()):
        row = match_row_for_text_suggestion(
            questions,
            suggested_key=suggested_key,
            missing_fields=missing_fields,
        )

        mapped = map_question_to_model(row) if row else None

        return IntakeSessionFirstQuestion(
            key=mapped.key if mapped else "llm_followup",
            title=mapped.title if mapped else "",
            text=text,
            type=mapped.type if mapped else "text",
            options=mapped.options if mapped else None,
        )

    # Handle key suggestion
    if isinstance(suggested_key, str):
        if row := find_question_row_by_key(questions, suggested_key):
            return map_question_to_model(row)

    # Fallback
    if row := first_question_row_in_missing(questions, missing_fields):
        return map_question_to_model(row)

    return None


def _build_intake_parse_result(
    *,
    parsed_output: LlmParseModelOutput,
    question_keys: list[str],
    current_criteria: dict[str, Any],
    required_fields: list[str],
    previously_skipped: list[str],
) -> dict[str, Any]:
    allowed_keys = set(question_keys)
    extracted = {
        key: value for key, value in parsed_output.extracted.items() if key in allowed_keys
    }
    merged_criteria = {**current_criteria, **extracted}

    skipped_fields = sorted(
        {*previously_skipped, *parsed_output.skipped_fields} & set(required_fields),
    )

    missing_fields = merge_missing_fields(
        merged_criteria=merged_criteria,
        required_fields=required_fields,
        model_missing=parsed_output.missing_fields,
        skipped_fields=skipped_fields,
    )

    if skipped_fields:
        merged_criteria = {**merged_criteria, SKIPPED_FIELDS_KEY: skipped_fields}

    next_question = parsed_output.next_question.model_dump()
    is_complete = len(missing_fields) == 0

    return {
        "extracted": extracted,
        "merged_criteria": merged_criteria,
        "missing_fields": missing_fields,
        "skipped_fields": skipped_fields,
        "next_question": next_question,
        "is_complete": is_complete,
    }
