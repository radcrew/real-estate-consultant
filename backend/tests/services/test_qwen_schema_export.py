"""The Qwen image's schemas must match the Pydantic models they were exported from."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.export_qwen_schemas import EXPORTED_SCHEMAS, SCHEMA_DIR, render


class TestQwenSchemaExport:
    @pytest.mark.parametrize("name", sorted(EXPORTED_SCHEMAS))
    def test_committed_schema_matches_the_model(self, name):
        """Drift here is silent in production.

        The image compiles these into GBNF at build time, so a model that gained a field
        without a re-export leaves the decoder constrained to the old shape: the new
        field can never be emitted, no error is raised anywhere, and the value simply
        goes missing. Re-run ``python scripts/export_qwen_schemas.py``.
        """
        path = SCHEMA_DIR / f"{name}.json"
        assert path.exists(), f"{path} is missing; run scripts/export_qwen_schemas.py"
        assert path.read_text(encoding="utf-8") == render(EXPORTED_SCHEMAS[name])

    def test_every_committed_schema_is_still_exported(self):
        """A stale file would be compiled into a grammar nothing routes to."""
        committed = {path.stem for path in SCHEMA_DIR.glob("*.json")}
        assert committed == set(EXPORTED_SCHEMAS)

    def test_schema_dir_resolves_inside_the_image_context(self):
        expected = Path(__file__).resolve().parents[3] / "services" / "qwen-lambda" / "schemas"
        assert SCHEMA_DIR == expected

    def test_intake_schema_declares_an_object_envelope(self):
        """The grammar is generated from this, so the top level has to be an object."""
        schema = json.loads((SCHEMA_DIR / "LlmParseModelOutput.json").read_text(encoding="utf-8"))
        assert schema["type"] == "object"
        assert set(schema["properties"]) == {
            "extracted",
            "missing_fields",
            "skipped_fields",
            "next_question",
            "is_complete",
        }

    def test_extracted_stays_open(self):
        """Question keys live in the database, so the grammar cannot enumerate them.

        The backend filters ``extracted`` against the real questions after parsing; if
        this ever became a closed object, the grammar would start silently dropping
        answers whenever the questions table changed.
        """
        schema = json.loads((SCHEMA_DIR / "LlmParseModelOutput.json").read_text(encoding="utf-8"))
        assert schema["properties"]["extracted"]["additionalProperties"] is True
