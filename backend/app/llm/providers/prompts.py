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
    "- ``missing_fields`` must list only keys still missing from required criteria "
    "(see required_fields in the user message) that are worth asking about.\n"
    "- ``skipped_fields`` must list required keys the user explicitly declined to "
    "answer (e.g. 'no preference', 'doesn't matter', 'skip that', 'not important to me'). "
    "Once a field is in skipped_fields, never put it in missing_fields or next_question "
    "again, and never ask about it again. The user message also lists "
    "previously_skipped_fields — always include those keys in skipped_fields too.\n"
    "- A key must never appear in both missing_fields and skipped_fields.\n"
    "- ``next_question.key`` should be one of question_keys when possible, "
    "ideally the first entry in missing_fields. Do not suggest a question for a key "
    "in skipped_fields or already present in current_criteria/extracted.\n"
    "- ``next_question.text`` should be concise and conversational. If missing_fields "
    "is empty, leave next_question.key and next_question.text empty/null.\n"
    "- ``is_complete`` should be true once missing_fields is empty (everything is "
    "either answered or skipped)."
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

