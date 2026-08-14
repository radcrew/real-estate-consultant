"""Download GGUF weights from Hugging Face into ``model/``.

Runs on your machine (or CI) before ``docker build``, not inside it: the image would
otherwise need a Hugging Face token at build time, and a token passed as a build arg is
readable in the image layers forever.

    pip install -r requirements-build.txt
    python fetch_model.py --repo-id Qwen/Qwen2.5-0.5B-Instruct-GGUF

A private repository needs ``HF_TOKEN`` in the environment; the download is anonymous
otherwise.
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

GGUF_SUFFIX = ".gguf"
DEFAULT_OUT = Path(__file__).resolve().parent / "model" / "qwen.gguf"


class NoGgufFound(RuntimeError):
    """The repository holds weights, but not in the format llama.cpp can load."""


def select_gguf(files: list[str], *, filename: str | None = None) -> str:
    """Pick which GGUF to download, refusing to guess between quantisations.

    Quantisation is a measured trade (see README §1), so a repository offering several
    is an explicit choice — picking "the first one" here would silently decide accuracy
    and image size on the caller's behalf.
    """
    candidates = sorted(name for name in files if name.lower().endswith(GGUF_SUFFIX))
    if filename:
        if filename not in files:
            raise NoGgufFound(
                f"{filename!r} is not in the repository. Available GGUF files: "
                f"{candidates or 'none'}."
            )
        return filename
    if not candidates:
        raise NoGgufFound(
            "No .gguf file in this repository. If it holds safetensors, convert first:\n"
            "  git clone https://github.com/ggerganov/llama.cpp\n"
            "  python llama.cpp/convert_hf_to_gguf.py <local-model-dir> \\\n"
            "      --outfile model/qwen.gguf --outtype q8_0\n"
            "then build without --repo-id."
        )
    if len(candidates) > 1:
        raise NoGgufFound(
            "Several GGUF files here; choose one with --filename:\n  "
            + "\n  ".join(candidates)
        )
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-id", required=True, help="e.g. Qwen/Qwen2.5-0.5B-Instruct-GGUF")
    parser.add_argument("--filename", default=None, help="Which .gguf, when the repo has several")
    parser.add_argument("--revision", default=None, help="Pin a commit rather than tracking main")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    # Imported here so the selection logic above stays importable — and testable —
    # without the Hugging Face client installed.
    from huggingface_hub import hf_hub_download, list_repo_files

    token = os.environ.get("HF_TOKEN") or None
    files = list_repo_files(args.repo_id, revision=args.revision, token=token)
    chosen = select_gguf(files, filename=args.filename)
    print(f"Downloading {args.repo_id}/{chosen}")

    cached = hf_hub_download(
        repo_id=args.repo_id,
        filename=chosen,
        revision=args.revision,
        token=token,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Copy rather than symlink: docker build cannot follow a link out of the context.
    shutil.copyfile(cached, args.out)
    size_mb = args.out.stat().st_size / (1024 * 1024)
    print(f"Wrote {args.out} ({size_mb:.0f} MB)")


if __name__ == "__main__":
    main()
