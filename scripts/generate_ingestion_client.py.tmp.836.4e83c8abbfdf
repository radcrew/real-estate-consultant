#!/usr/bin/env python
"""Regenerate the backend's typed ingestion-service client from its OpenAPI schema.

Usage:
    python scripts/generate_ingestion_client.py

Run this after changing any request/response model under
``services/ingestion/app/schemas`` or ``services/ingestion/app/api``, then commit
the regenerated files. CI re-runs this script and fails the build if the output
differs from what's committed (contract drift caught before it reaches production).

Requires the ingestion service's runtime dependencies (to import its FastAPI app)
and ``datamodel-code-generator`` (backend dev dependency).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGESTION_ROOT = ROOT / "services" / "ingestion"
OPENAPI_PATH = INGESTION_ROOT / "openapi.json"
MODELS_PATH = ROOT / "backend" / "app" / "clients" / "ingestion" / "models.py"


def export_openapi_schema() -> dict:
    # The ingestion service requires these at import time; values don't matter
    # for schema generation, so use placeholders if not already set.
    os.environ.setdefault("SUPABASE_URL", "https://placeholder.supabase.co")
    os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "placeholder")
    sys.path.insert(0, str(INGESTION_ROOT))
    from app.main import app

    return app.openapi()


def main() -> None:
    schema = export_openapi_schema()
    OPENAPI_PATH.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OPENAPI_PATH.relative_to(ROOT)}")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(OPENAPI_PATH),
            "--input-file-type",
            "openapi",
            "--output",
            str(MODELS_PATH),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.11",
            "--disable-timestamp",
        ],
        check=True,
    )

    # Match the backend's formatting (ruff defaults to double quotes) so the
    # generated file doesn't churn the diff on every regeneration.
    subprocess.run([sys.executable, "-m", "ruff", "format", str(MODELS_PATH)], check=True)
    print(f"Wrote {MODELS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
