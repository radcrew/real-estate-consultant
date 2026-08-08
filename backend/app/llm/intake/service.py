"""Intake orchestration: LLM provider calls and next-question resolution."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.domain.bounds import correct_bound_direction
from app.domain.intake_criteria import (
    drop_placeholder_values,
    drop_self_describing_values,
    drop_unconfigured_choices,
)
from app.domain.intake_next_question import (
    first_question_row_in_missing,
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
from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.schemas.llm_intake_parse import LlmOpeningQuestionOutput, LlmParseModelOutput

QuestionRow = dict[str, Any]

# Reserved criteria key holding required fields the user explicitly declined to answer.
SKIPPED_FIELDS_KEY = "_skipped_fields"

# Decode settings for criteria extraction. Named so ``ml/eval`` scores the same decode
# production runs; changing one here changes both.
INTAKE_PARSE_TEMPERATURE = 0.1
INTAKE_PARSE_MAX_TOKENS = 800


@dataclass(frozen=True)
class IntakePrompt:
    """The extraction request, plus the derived context needed to score its reply."""

    messages: list[dict[str, Any]] = field(default_factory=list)
    question_keys: list[str] = field(default_factory=list)
    required_fields: list[str] = field(default_factory=list)
    previously_skipped: list[str] = field(default_factory=list)
    criteria_for_prompt: dict[str, Any] = field(default_factory=dict)


def build_intake_messages(
    *,
    user_input: str,
    current_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> IntakePrompt:
    """Build the criteria-extraction request sent for one intake turn.

    Shared with ``ml/eval`` so the harness cannot score a prompt production never sends.
    Constant content (schema, rules) stays ahead of variable content (the turn payload)
    so a served prefix cache keeps hitting.
    """
    question_keys, required_fields = extract_question_keys(questions)
    previously_skipped = [
        key for key in current_criteria.get(SKIPPED_FIELDS_KEY, []) if isinstance(key, str)
    ]
    criteria_for_prompt = {k: v for k, v in current_criteria.items() if k != SKIPPED_FIELDS_KEY}

    intake_schema = render_intake_response_schema(questions=questions)
    system_prompt = (
        f"{INTAKE_PARSE_SYSTEM_PROMPT_HEADER}{intake_schema}\n"
        f"{INTAKE_PARSE_SYSTEM_PROMPT_RULES}"
    )
    user_prompt = json.dumps(
        {
            "user_input": user_input,
            "current_criteria": criteria_for_prompt,
            "question_keys": question_keys,
            "required_fields": required_fields,
            "previously_skipped_fields": previously_skipped,
        },
        ensure_ascii=True,
    )
    return IntakePrompt(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        question_keys=question_keys,
        required_fields=required_fields,
        previously_skipped=previously_skipped,
        criteria_for_prompt=criteria_for_prompt,
    )


async def parse_user_input(
    *,
    user_input: str,
    current_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Parse free-form user intake input into structured criteria and next-step hints."""
    prompt = build_intake_messages(
        user_input=user_input,
        current_criteria=current_criteria,
        questions=questions,
    )
    # Only this call site takes the override. generate_opening_question, fit and
    # outreach stay on the configured default, so a small pinned model never writes prose.
    override = settings.intake_chat_override
    model, base_url, api_key = override if override else (None, None, None)

    parsed_output = await generate_structured_output(
        messages=prompt.messages,
        response_format=LlmParseModelOutput,
        temperature=INTAKE_PARSE_TEMPERATURE,
        max_tokens=INTAKE_PARSE_MAX_TOKENS,
        # The system prompt already carries the intake schema; a second copy of the
        # Pydantic schema would be ~1k characters of duplicate prompt per turn.
        include_schema_instruction=False,
        model=model,
        base_url=base_url,
        api_key=api_key,
    )
    return _build_intake_parse_result(
        parsed_output=parsed_output,
        user_input=user_input,
        questions=questions,
        question_keys=prompt.question_keys,
        current_criteria=prompt.criteria_for_prompt,
        required_fields=prompt.required_fields,
        previously_skipped=prompt.previously_skipped,
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
    """Pick the next question from ``missing_fields``, using the configured wording.

    ``suggested_question`` is accepted and deliberately ignored. The model is still asked
    for it — see ``build_intake_response_schema`` — because the tuned adapter emits
    malformed JSON without the field, but nothing it writes there is used.

    Four defects came from trusting that text. It is composed from the turn alone, with
    no knowledge of what the backend recorded, so it asked for a field the same turn had
    just filled in, echoed the user's own sentence back as a question, merged two
    questions into one, and copied the schema's own description into a reply.
    ``questions.json`` holds the wording and cannot get any of that wrong.
    """
    if not missing_fields:
        return None

    row = first_question_row_in_missing(questions, missing_fields)
    return map_question_to_model(row) if row else None


def _build_intake_parse_result(
    *,
    parsed_output: LlmParseModelOutput,
    user_input: str,
    questions: list[QuestionRow],
    question_keys: list[str],
    current_criteria: dict[str, Any],
    required_fields: list[str],
    previously_skipped: list[str],
) -> dict[str, Any]:
    allowed_keys = set(question_keys)
    extracted = {
        key: value for key, value in parsed_output.extracted.items() if key in allowed_keys
    }
    # Keys are filtered above, values here. Both run before merge_missing_fields on
    # purpose: a filler value, or a choice the questionnaire does not offer, must leave
    # the field *missing* rather than answered, or the session completes on something
    # search cannot use and the question is never asked.
    extracted = drop_placeholder_values(extracted)
    extracted = drop_self_describing_values(extracted, questions)
    extracted = drop_unconfigured_choices(extracted, questions)
    # The model reads the figure reliably and the comparator unreliably, so the side a
    # lone bound sits on is decided here from the message itself. No-op unless the
    # message states one direction and the model chose the other.
    extracted = correct_bound_direction(extracted, user_input)
    merged_criteria = {**current_criteria, **extracted}

    # Union carries a skip forward across turns, so the user is never re-asked. Then
    # subtract what is answered: a field the user has since filled in is no longer
    # skipped, and without this it stays marked skipped for the life of the session.
    # A required field is answered, skipped, or missing - never two of those at once.
    skipped_fields = sorted(
        ({*previously_skipped, *parsed_output.skipped_fields} & set(required_fields))
        - set(merged_criteria),
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
