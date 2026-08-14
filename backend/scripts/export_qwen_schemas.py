"""Export the structured-output schemas the Qwen Lambda image compiles into grammars.

Run from ``backend/`` whenever one of the exported models changes::

    python scripts/export_qwen_schemas.py

The Pydantic model is the single source of truth: the image turns these JSON Schemas
into GBNF at build time (``infra/qwen-lambda/build_grammars.py``), so a model edited
without re-running this leaves the decoder constrained to the previous shape — the new
field simply never appears, with no error anywhere. ``test_qwen_schema_export`` fails on
that drift.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas.llm_intake_parse import LlmParseModelOutput

# Keyed by the ``schema_name`` the provider sends, which is the Pydantic class name.
EXPORTED_SCHEMAS = {
    "LlmParseModelOutput": LlmParseModelOutput,
}

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "infra" / "qwen-lambda" / "schemas"


def render(model: type) -> str:
    """Serialise deterministically, so an unchanged model produces no diff."""
    return json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in EXPORTED_SCHEMAS.items():
        path = SCHEMA_DIR / f"{name}.json"
        path.write_text(render(model), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
