"""What a dataset or an adapter was made from, written down beside it.

    python -m pipeline.provenance                       # every stamp found
    python -m pipeline.provenance <a> <b>               # what differs between two

A training cycle was lost to a question nobody could answer from the artefacts: v7 came
back worse than v6, and the reason was that it had been regenerated at the default
``--count 2500`` rather than v6's ``--count 3000`` — 2,250 rows against 2,700, a 17% cut.
Nothing beside the weights recorded which, so the only way to find it was to diff two
``train.jsonl`` files that had already been overwritten once.

Everything here is stdlib. A stamp has to be readable from a checkout with no venv, and a
provenance record that needs torch installed to be read is not a record.

Two rules the format follows:

**Hashes over paths.** ``train.jsonl`` is one path holding a different file every
revision, so a stamp naming it says nothing. The sha256 does, and it is what lets the
trainer notice it is reading data the dataset stamp does not describe.

**Never fail the job.** Provenance is bookkeeping wrapped around work that costs hours.
Git missing, a file unreadable, a directory not writable — each degrades to a null in the
record. A stamp that aborts a finished training run would be worse than no stamp.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pipeline.paths import DATASETS_DIR, MODELS_DIR, REPO_ROOT

# Written next to the thing it describes, so a copied directory carries its own history.
DATASET_STAMP_NAME = "dataset_provenance.json"
ADAPTER_STAMP_NAME = "training_provenance.json"


def file_digest(path: Path | str) -> str | None:
    """sha256 of a file, or None if it cannot be read."""
    try:
        digest = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                digest.update(block)
        return digest.hexdigest()
    except OSError:
        return None


def line_count(path: Path | str) -> int | None:
    """Non-blank lines in a text file, or None if it cannot be read.

    ``errors="replace"``, because this counts lines and does not care what is on them. A
    byte that is not UTF-8 raises ``UnicodeDecodeError``, which is a ``ValueError`` and
    not an ``OSError``, so it escaped the guard entirely -- breaking the module's "never
    fail the job" rule at the worst possible moment. ``write_adapter_stamp`` calls this on
    the train and validation paths *after* ``trainer.train()`` and ``save_pretrained()``,
    so a ``train.jsonl`` written by any tool that does not force ASCII would have crashed
    the end of a multi-hour run over a line count. ``eval/run.py`` has the same exposure
    through an arbitrary ``--dataset``.
    """
    try:
        with Path(path).open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return None


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_state() -> dict[str, Any]:
    """The commit this was built from, and whether the tree had uncommitted changes.

    ``dirty`` matters more than the SHA. Most of these runs happen mid-change, so a stamp
    reading ``commit abc123, dirty true`` is honest about the SHA not being the whole
    story — and a stamp reading ``dirty false`` means the commit really does reproduce it.
    """
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": None if status is None else bool(status),
    }


def _write(path: Path, payload: dict[str, Any]) -> Path | None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"could not write provenance to {path}: {exc}", file=sys.stderr)
        return None
    return path


def read_stamp(path: Path | str) -> dict[str, Any] | None:
    """Load a stamp from a file or from the directory holding one, or None."""
    candidate = Path(path)
    if candidate.is_dir():
        for name in (DATASET_STAMP_NAME, ADAPTER_STAMP_NAME):
            if (candidate / name).exists():
                candidate = candidate / name
                break
        else:
            return None
    try:
        loaded = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def write_dataset_stamp(
    *,
    out_dir: Path,
    args: dict[str, Any],
    inputs: dict[str, Path],
    outputs: dict[str, Path],
    counts: dict[str, Any],
    note: str | None = None,
) -> Path | None:
    """Record what produced ``train.jsonl`` and ``validation.jsonl``.

    ``args`` is the generator's own flags — ``--count`` and ``--seed`` above all, the two
    that silently change the dataset without changing a line of code.

    ``note`` is for a stamp written by hand rather than by the generator, which is only
    honest if it says so: a reconstructed record that reads like an observed one is worse
    than none at all.
    """
    payload = {
        "kind": "dataset",
        "generated_by": "pipeline.data.generate",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git": git_state(),
        "note": note,
        "args": args,
        "counts": counts,
        "inputs": {
            name: {"path": _relative(path), "sha256": file_digest(path)}
            for name, path in inputs.items()
        },
        "outputs": {
            name: {
                "path": _relative(path),
                "sha256": file_digest(path),
                "rows": line_count(path),
            }
            for name, path in outputs.items()
        },
    }
    return _write(out_dir / DATASET_STAMP_NAME, payload)


def write_adapter_stamp(
    *,
    out_dir: Path,
    base_model: str,
    hyperparameters: dict[str, Any],
    train_path: Path,
    val_path: Path,
    counts: dict[str, Any],
    versions: dict[str, Any],
) -> Path | None:
    """Record what an adapter was trained on, beside the weights.

    The dataset stamp is copied in rather than referenced. ``train.jsonl`` is regenerated
    in place every revision, so a pointer to it goes stale the next time the generator
    runs — which is exactly when the question gets asked.

    ``dataset_matches_stamp`` is the part worth reading. It compares the hash of the file
    actually trained on against the hash the dataset stamp recorded. False means the data
    was regenerated after the stamp was written, and everything the stamp says about
    ``--count`` and row counts describes a different file.
    """
    dataset = read_stamp(train_path.parent)
    recorded = ((dataset or {}).get("outputs") or {}).get("train") or {}
    trained_on = file_digest(train_path)
    payload = {
        "kind": "adapter",
        "generated_by": "pipeline.train.train_lora",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "git": git_state(),
        "base_model": base_model,
        "hyperparameters": hyperparameters,
        "counts": counts,
        "versions": versions,
        "trained_on": {
            "train": {"path": _relative(train_path), "sha256": trained_on,
                      "rows": line_count(train_path)},
            "validation": {"path": _relative(val_path), "sha256": file_digest(val_path),
                           "rows": line_count(val_path)},
        },
        "dataset_matches_stamp": (
            None if dataset is None or trained_on is None
            else recorded.get("sha256") == trained_on
        ),
        "dataset": dataset,
    }
    return _write(out_dir / ADAPTER_STAMP_NAME, payload)


def stamp_says_data_changed(stamp_path: Path | str) -> bool:
    """True when a written stamp records data that does not match its own dataset stamp.

    Only ``False`` counts. ``None`` means there was no dataset stamp to compare against —
    an older checkout, or data generated before this existed — and warning about that on
    every run would train people to ignore the warning that matters.
    """
    stamp = read_stamp(stamp_path)
    return bool(stamp) and stamp.get("dataset_matches_stamp") is False


def _relative(path: Path | str) -> str:
    """Repo-relative where possible, so stamps compare across clones."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


# Reading stamps back ----------------------------------------------------------------


def flatten(payload: Any, prefix: str = "") -> dict[str, Any]:
    """A nested stamp as dotted keys, so two of them can be compared key by key."""
    if isinstance(payload, dict):
        flat: dict[str, Any] = {}
        for key, value in payload.items():
            flat.update(flatten(value, f"{prefix}.{key}" if prefix else str(key)))
        return flat
    return {prefix: payload}


# Noise in every comparison: two runs always differ here and it never explains anything.
_ALWAYS_DIFFERS = ("generated_at",)


def differences(left: dict[str, Any], right: dict[str, Any]) -> list[tuple[str, Any, Any]]:
    """Every field the two stamps disagree on, timestamps excluded."""
    flat_left, flat_right = flatten(left), flatten(right)
    keys = sorted(set(flat_left) | set(flat_right))
    return [
        (key, flat_left.get(key, "-"), flat_right.get(key, "-"))
        for key in keys
        if flat_left.get(key, "-") != flat_right.get(key, "-")
        and not any(key.endswith(tail) for tail in _ALWAYS_DIFFERS)
    ]


def _summary(stamp: dict[str, Any]) -> str:
    git = stamp.get("git") or {}
    commit = (git.get("commit") or "unknown")[:8]
    dirty = "+dirty" if git.get("dirty") else ""
    counts = stamp.get("counts") or {}
    return (
        f"{stamp.get('kind', '?'):<8} {stamp.get('generated_at', '?'):<20} "
        f"{commit}{dirty:<6} {json.dumps(counts, separators=(',', ':'))}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="stamp files or directories holding one")
    args = parser.parse_args()

    if len(args.paths) == 2:
        left, right = (read_stamp(p) for p in args.paths)
        if left is None or right is None:
            print("need a stamp at both paths")
            return 1
        rows = differences(left, right)
        if not rows:
            print("identical apart from the timestamp")
            return 0
        width = max(len(key) for key, _, _ in rows)
        print(f"{'field'.ljust(width)}  {args.paths[0]}  ->  {args.paths[1]}")
        for key, was, now in rows:
            print(f"{key.ljust(width)}  {was}  ->  {now}")
        return 0

    searched = [Path(p) for p in args.paths] or [DATASETS_DIR, *_model_dirs()]
    found = 0
    for path in searched:
        stamp = read_stamp(path)
        if stamp is None:
            continue
        found += 1
        print(f"{_relative(path)}\n  {_summary(stamp)}")
    if not found:
        print("no provenance stamps found; regenerate the data or retrain to write one")
    return 0


def _model_dirs() -> list[Path]:
    try:
        return sorted(p for p in MODELS_DIR.iterdir() if p.is_dir())
    except OSError:
        return []


if __name__ == "__main__":
    raise SystemExit(main())
