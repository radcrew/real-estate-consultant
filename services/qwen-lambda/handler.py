"""Lambda handler for the fine-tuned Qwen2.5-0.5B criteria extractor.

Serves the contract ``app/llm/providers/qwen_lambda.py`` calls::

    in   {"messages": [...], "schema_name": "...", "max_tokens": n, "temperature": f}
    out  {"text": "...", "stop_reason": "stop"|"length",
          "usage": {"prompt_tokens": n, "completion_tokens": n}}

Generation is **grammar-constrained**: the sampler can only emit tokens that keep the
output valid against the schema, so malformed JSON is impossible rather than unlikely.
A 0.5B asked politely for JSON will eventually not produce it; this is the difference
between a model that passes testing and one that survives production.

The grammar constrains the *envelope* only. ``extracted`` is an open object, so the
grammar cannot check that its keys are real question keys — the backend validates that
after parsing, against the questions actually in the database.
"""

from __future__ import annotations

import os
from typing import Any

from llama_cpp import Llama, LlamaGrammar

MODEL_PATH = os.environ.get("MODEL_PATH", "/var/task/model/qwen.gguf")
GRAMMAR_DIR = os.environ.get("GRAMMAR_DIR", "/var/task/grammars")
N_CTX = int(os.environ.get("N_CTX", "4096"))
# 0 lets llama.cpp pick. Lambda scales vCPU with memory, so the useful value tracks the
# function's memory setting rather than being fixed here.
N_THREADS = int(os.environ.get("N_THREADS", "0")) or None

DEFAULT_MAX_TOKENS = 800
DEFAULT_TEMPERATURE = 0.1


def build_llm() -> Llama:
    """Load the weights. ``mmap`` keeps this to a page-in rather than a full read."""
    return Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_threads=N_THREADS,
        use_mmap=True,
        verbose=False,
    )


def load_grammars(directory: str = GRAMMAR_DIR) -> dict[str, LlamaGrammar]:
    """Load every GBNF compiled into the image, keyed by schema name."""
    grammars: dict[str, LlamaGrammar] = {}
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".gbnf"):
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as handle:
            grammars[name[: -len(".gbnf")]] = LlamaGrammar.from_string(
                handle.read(), verbose=False
            )
    return grammars


def generate(
    event: dict[str, Any],
    *,
    llm: Llama,
    grammars: dict[str, LlamaGrammar],
) -> dict[str, Any]:
    """Run one constrained completion.

    Raises on a malformed request rather than returning an error object: an exception
    sets Lambda's ``FunctionError``, which is what the caller classifies on. Returning
    ``{"error": ...}`` with a 200 would look like a successful invocation.
    """
    messages = event.get("messages")
    if not isinstance(messages, list) or not messages:
        raise ValueError("'messages' must be a non-empty list.")

    schema_name = event.get("schema_name")
    grammar = grammars.get(schema_name) if isinstance(schema_name, str) else None
    if grammar is None:
        raise ValueError(
            f"No grammar for schema_name {schema_name!r}. "
            f"This image was built with: {sorted(grammars) or 'none'}."
        )

    completion = llm.create_chat_completion(
        messages=messages,
        grammar=grammar,
        max_tokens=int(event.get("max_tokens") or DEFAULT_MAX_TOKENS),
        temperature=float(event.get("temperature", DEFAULT_TEMPERATURE)),
    )

    choice = (completion.get("choices") or [{}])[0]
    usage = completion.get("usage") or {}
    return {
        "text": (choice.get("message") or {}).get("content") or "",
        # The caller treats "length" as an incomplete reply: the grammar guarantees the
        # shape of what was emitted, not that the model finished emitting it.
        "stop_reason": "length" if choice.get("finish_reason") == "length" else "stop",
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
        },
    }


# Built at import, so a warm environment pays for it once rather than per request.
# Absent files mean this module was imported outside the image — by tests or tooling,
# which supply their own — so importing must not fail.
LLM = build_llm() if os.path.exists(MODEL_PATH) else None
GRAMMARS = load_grammars() if os.path.isdir(GRAMMAR_DIR) else {}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    if LLM is None:
        raise RuntimeError(f"No model at {MODEL_PATH}: the image was built without weights.")
    return generate(event, llm=LLM, grammars=GRAMMARS)
