"""Load and validate LoopNet-style listing JSON from the backend dataset folder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DATA_PATH = _BACKEND_ROOT / "dataset" / "raw-data.json"


def load_listings(path: Path | None = None) -> list[dict[str, Any]]:
    """Parse the default (or given) raw JSON file: root must be an array of objects."""
    resolved = DEFAULT_RAW_DATA_PATH if path is None else path
    if not resolved.is_file():
        msg = f"Dataset file not found: {resolved}"
        raise FileNotFoundError(msg)

    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"Expected a JSON array at root, got {type(data).__name__}"
        raise ValueError(msg)

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            msg = f"Item at index {i} must be an object, got {type(item).__name__}"
            raise ValueError(msg)

    return data
