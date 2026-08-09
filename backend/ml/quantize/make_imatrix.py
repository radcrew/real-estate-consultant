"""Build an importance matrix from our own training data, for P6 quantization.

    cd backend
    python -m ml.quantize.make_imatrix --gguf qwen2.5-0.5b-instruct-intake-f16.gguf

Writes ``calibration.txt`` and ``imatrix.dat`` beside the GGUFs, then:

    python -m ml.quantize.build_gguf --model <merged-dir> --imatrix .local/models/imatrix.dat

``llama-quantize`` decides which weights tolerate 4 bits. Left to itself it uses a generic
notion of importance; given an imatrix it uses activations measured on text you supply.
Calibrating on the intake prompts specifically is the case where this pays, because the
model only ever sees this one prompt shape in production.

The calibration text is the **training** split, never the eval split. Calibrating on data
you also score against would quietly launder eval information into the artifact.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ml.paths import LLAMA_BIN_DIR, MODELS_DIR, TRAIN_PATH, llama_exe


def build_calibration(train_path: Path, out_path: Path, limit: int) -> int:
    """Render chat records to plain text, one example per chunk."""
    if not train_path.exists():
        raise SystemExit(f"no training data at {train_path}; run ml.data.generate first")

    chunks: list[str] = []
    for line in train_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        messages = json.loads(line)["messages"]
        chunks.append("\n".join(f"{m['role']}: {m['content']}" for m in messages))
        if len(chunks) >= limit:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n\n".join(chunks), encoding="utf-8")
    return len(chunks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gguf", required=True, help="F16 GGUF filename or path")
    parser.add_argument("--models-dir", default=str(MODELS_DIR))
    parser.add_argument("--llama-bin", default=str(LLAMA_BIN_DIR))
    parser.add_argument("--train", default=str(TRAIN_PATH))
    parser.add_argument(
        "--limit",
        type=int,
        default=400,
        help="Calibration examples. A few hundred of the right shape beats thousands",
    )
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    gguf = Path(args.gguf)
    if not gguf.is_absolute():
        gguf = models_dir / args.gguf
    if not gguf.exists():
        print(f"GGUF not found: {gguf}", file=sys.stderr)
        return 1

    exe = llama_exe("llama-imatrix", args.llama_bin)

    calibration = models_dir / "calibration.txt"
    count = build_calibration(Path(args.train), calibration, args.limit)
    size_kb = calibration.stat().st_size / 1024
    print(f"calibration: {count} examples, {size_kb:.0f} KB -> {calibration}")

    out = Path(args.out) if args.out else models_dir / "imatrix.dat"
    cmd = [
        str(exe),
        "-m", str(gguf),
        "-f", str(calibration),
        "-o", str(out),
        "-t", str(args.threads),
    ]
    print(f"\n$ {' '.join(cmd)}\n", flush=True)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        return result.returncode

    print(f"\nimatrix -> {out}")
    print("Next: ml.quantize.build_gguf --imatrix on the merged model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
