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
    "- Keep ``extracted`` sparse: include a property ONLY when this message states it. "
    "Omit every property you are unsure about. Never guess, never copy defaults, and "
    "never fill a property with the option list from the schema.\n"
    "- Every key you emit must come from question_keys. Never invent a key.\n"
    "- SKIP DETECTION (highest priority rule): if the user's message signals they do not "
    "want to answer the current topic — any refusal phrasing, however worded — you MUST "
    "add that question's key to ``skipped_fields`` immediately, and never re-ask it. "
    "``skipped_fields`` holds question keys only, never phrases from the message.\n"
    "- ``previously_skipped_fields`` in the user message lists keys already skipped. "
    "Copy each one into ``skipped_fields`` — unless this message answers it, in which "
    "case put the value in ``extracted`` and leave the key out of ``skipped_fields``.\n"
    "- Do not write a follow-up question. The backend chooses what to ask next."
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

