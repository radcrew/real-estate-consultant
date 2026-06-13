"""Prompt templates and small builders for the Hugging Face provider."""

from __future__ import annotations

# Intake parse: fixed instructions; inject ``json_schema`` between header and rules.
INTAKE_PARSE_SYSTEM_PROMPT_HEADER = (
    "You parse user real-estate search prompts into structured JSON.\n"
    "Return ONLY one JSON object that validates against this JSON Schema "
    "(no markdown fences, no commentary):\n"
)

INTAKE_PARSE_SYSTEM_PROMPT_RULES = (
    "Rules:\n"
    "- Keep ``extracted`` sparse: omit properties when unknown.\n"
    "- SKIP DETECTION (highest priority rule): if the user's message signals they do not "
    "want to answer the current topic — ANY phrasing like 'skip', 'pass', 'move on', "
    "'don't want to answer', 'not important', 'doesn't matter', 'no preference', "
    "'next question', 'let's move on', 'I don't care', 'skip that', or any similar "
    "refusal — you MUST add the relevant question key to ``skipped_fields`` immediately. "
    "Do NOT re-ask or rephrase the same question. Do NOT put it in ``missing_fields``. "
    "Move to the next unanswered, non-skipped field instead.\n"
    "- ``previously_skipped_fields`` in the user message lists fields already skipped. "
    "ALWAYS copy every key from previously_skipped_fields into ``skipped_fields`` — "
    "never ask about them again under any circumstances.\n"
    "- A key must NEVER appear in both missing_fields and skipped_fields.\n"
    "- ``missing_fields`` must list only required keys (from required_fields) that are "
    "not yet in current_criteria/extracted AND not in skipped_fields.\n"
    "- ``next_question.key`` should be the first key in missing_fields. "
    "NEVER pick a key from skipped_fields or already answered criteria.\n"
    "- ``next_question.text`` should be concise and conversational. "
    "If missing_fields is empty, set both key and text to null.\n"
    "- ``is_complete`` should be true once missing_fields is empty."
)

OPENING_QUESTION_SYSTEM_PROMPT_BASE = (
    "You write one short, friendly question for a commercial real-estate intake chatbot.\n"
    'Return ONLY valid JSON: {"text": string}\n'
    "The question should invite the user to describe what they are looking for in "
    "natural language.\n"
    "Do not repeat the entire welcome message; write only the question line "
    "(one or two sentences max)."
)

OPENING_QUESTION_OPTIONS_HINT = (
    "\nIf question_options lists choices, phrase the question so the user can select "
    "from those options (you may name the options briefly) "
    "or add a short clarification."
)

