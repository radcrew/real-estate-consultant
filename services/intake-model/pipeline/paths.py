"""Repo-relative locations and llama.cpp binary lookup, in one place.

Five modules each computed ``Path(__file__).resolve().parents[3]`` for the repo root, and
three wrote out the same Windows-aware executable search. That is one hard-coded directory
depth per file: moving this package a level, or adding a subpackage, silently repoints the
defaults, and because they are ``argparse`` defaults the break surfaces as "model not
found" in a different module than the one that moved.

That is not hypothetical — the move out of the backend tree into
``services/intake-model/pipeline/`` added a level and turned ``BACKEND_DIR`` from a
parent into a sibling lookup. One file changed.

Depth is now asserted in ``tests/test_paths.py`` rather than repeated.

Nothing here touches the filesystem at import time — these are locations, not guarantees
that anything exists. ``llama_exe`` is the exception, because "which binary would run" has
no meaning without looking.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# pipeline/paths.py -> pipeline/ -> intake-model/ -> services/ -> repo root.
# Kept as parents[2] in exactly one file.
PACKAGE_DIR = Path(__file__).resolve().parent
SERVICE_DIR = PACKAGE_DIR.parent
REPO_ROOT = PACKAGE_DIR.parents[2]

# Named rather than derived from ``PACKAGE_DIR``: this package no longer lives under
# ``backend/``, so the backend is a sibling looked up from the root, not a parent walked
# up to. ``app`` is importable because the backend is installed into this venv (see
# pyproject), not because of where these directories sit.
BACKEND_DIR = REPO_ROOT / "backend"

# Untracked scratch space for weights, GGUFs and llama.cpp itself. Deliberately outside
# backend/ so nothing here can be swept into a deploy.
LOCAL_DIR = REPO_ROOT / ".local"
MODELS_DIR = LOCAL_DIR / "models"
LLAMA_BIN_DIR = LOCAL_DIR / "bin"
LLAMA_SRC_DIR = LOCAL_DIR / "llama.cpp"

DATA_DIR = PACKAGE_DIR / "data"
EVAL_DIR = PACKAGE_DIR / "eval"

QUESTIONS_PATH = EVAL_DIR / "questions.json"
EVAL_DATASET_PATH = EVAL_DIR / "dataset.jsonl"
RESULTS_DIR = EVAL_DIR / "results"
TRAIN_PATH = DATA_DIR / "train.jsonl"
VAL_PATH = DATA_DIR / "validation.jsonl"
PHRASINGS_PATH = DATA_DIR / "property_type_phrasings.json"


def llama_exe(name: str, bin_dir: Path | str | None = None) -> Path:
    """Resolve a llama.cpp binary, preferring the pinned build over one on PATH.

    ``.local/bin`` holds the build the results tables were measured against, so it wins:
    a system llama.cpp of another version would produce numbers that cannot be compared
    with the rows already recorded. PATH is the fallback rather than the default.

    Raises ``SystemExit`` when neither exists — every caller treats a missing binary as
    fatal, and three of them previously duplicated that check with slightly different
    wording. Only ``build_gguf`` used to fall back to PATH at all, so a system-installed
    ``llama-server`` failed where a system-installed ``llama-quantize`` worked.
    """
    directory = Path(bin_dir) if bin_dir is not None else LLAMA_BIN_DIR
    exe = directory / (f"{name}.exe" if sys.platform == "win32" else name)
    if exe.exists():
        return exe
    if found := shutil.which(name):
        return Path(found)
    raise SystemExit(f"{name} not found at {exe} or on PATH")
