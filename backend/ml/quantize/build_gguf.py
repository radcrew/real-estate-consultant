"""Fetch, convert and quantize an intake model into GGUFs llama.cpp can serve.

Scripted rather than remembered: the flags below decide what a results row means, and
they get lost between runs otherwise.

    cd backend
    python -m ml.quantize.build_gguf --model Qwen/Qwen2.5-0.5B-Instruct

Produces, under ``--out`` (default ``<repo>/.local/models``):

    Qwen2.5-0.5B-Instruct/              the HF snapshot
    qwen2.5-0.5b-instruct-f16.gguf      conversion only, no quantization
    qwen2.5-0.5b-instruct-q4_k_m.gguf   what would actually be served

The pair matters: F16 against Q4_K_M isolates what quantization alone costs, before any
fine-tuning is in the picture. Measuring them together makes a regression unattributable.

Add ``--imatrix`` at P6 to quantize with an importance matrix and protected embedding and
output tensors. It is deliberately off for the P2 stock baseline, so the baseline
measures plain Q4_K_M and nothing else.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ml.paths import LLAMA_BIN_DIR, LLAMA_SRC_DIR, MODELS_DIR, llama_exe

LLAMA_REPO = "https://github.com/ggml-org/llama.cpp.git"
# Pin the converter to the same build as the binaries in .local/bin. Conversion output
# is version-sensitive, so a drifting master is a silent source of unreproducible GGUFs.
DEFAULT_LLAMA_TAG = "b10290"


def run(cmd: list[str], **kwargs) -> None:
    print(f"\n$ {' '.join(str(c) for c in cmd)}\n", flush=True)
    subprocess.run(cmd, check=True, **kwargs)


def _is_local_path(model_id: str) -> bool:
    """True when ``--model`` names a directory rather than a Hub repo id.

    Hub ids are ``name`` or ``namespace/name``: at most one forward slash, never
    absolute, no backslashes, no leading dot.
    """
    return (
        Path(model_id).is_absolute()
        or "\\" in model_id
        or model_id.startswith(".")
        or model_id.count("/") > 1
    )


def snapshot(model_id: str, out_dir: Path) -> Path:
    """Resolve ``--model`` to a directory of full weights.

    Accepts a Hub repo id or a local directory — ``ml.train.merge`` output is passed
    this way at P6. A local-looking path that does not exist fails here rather than
    falling through to the Hub, which would report it as an invalid repo id and send
    you looking in the wrong place.
    """
    if _is_local_path(model_id):
        local = Path(model_id).resolve()
        if not local.is_dir():
            raise SystemExit(
                f"no model directory at {local}\n"
                "Run ml.train.train_lora and then ml.train.merge first: "
                "convert_hf_to_gguf.py reads full weights, not a LoRA adapter."
            )
        if not any(local.glob("*.safetensors")):
            raise SystemExit(
                f"{local} contains no *.safetensors.\n"
                "That looks like an adapter directory, not a merged model. "
                "Run ml.train.merge --adapter <that dir> --out <merged dir>."
            )
        print(f"using local model: {local}")
        return local

    from huggingface_hub import snapshot_download

    target = out_dir / model_id.split("/")[-1]
    if target.exists() and any(target.glob("*.safetensors")):
        print(f"snapshot already present: {target}")
        return target
    print(f"downloading {model_id} -> {target}")
    snapshot_download(
        repo_id=model_id,
        local_dir=target,
        ignore_patterns=["*.pth", "*.bin", "*.gguf", "*.onnx", "original/*"],
    )
    return target


def ensure_convert_script(src_dir: Path, tag: str) -> Path:
    """Shallow-clone llama.cpp source for ``convert_hf_to_gguf.py``.

    The release zip ships binaries only, and the converter is no longer a standalone
    file — it imports a sibling ``conversion`` package — so a single-file download does
    not work. Pinned to ``tag`` to match the binaries.
    """
    script = src_dir / "convert_hf_to_gguf.py"
    if script.exists():
        return script
    src_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--depth", "1", "--branch", tag, LLAMA_REPO, str(src_dir)])
    if not script.exists():
        raise SystemExit(f"convert_hf_to_gguf.py not found after cloning {tag}")
    return script


def quantize_flags(kind: str, imatrix: Path | None) -> list[str]:
    """Flags for one quantization rung.

    At P6, ``--imatrix`` plus Q8_0 embedding and output tensors is the recipe: the ~152k
    vocabulary makes those tensors a large share of the parameters, and they are the ones
    emitting exact field values. Off by default so the stock baseline stays plain.
    """
    flags: list[str] = []
    if imatrix is not None:
        flags += [
            "--imatrix", str(imatrix),
            "--token-embedding-type", "q8_0",
            "--output-tensor-type", "q8_0",
        ]
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--out", default=str(MODELS_DIR))
    parser.add_argument("--llama-bin", default=str(LLAMA_BIN_DIR))
    parser.add_argument("--llama-src", default=str(LLAMA_SRC_DIR))
    parser.add_argument("--llama-tag", default=DEFAULT_LLAMA_TAG)
    parser.add_argument(
        "--quant",
        action="append",
        default=None,
        help="Quantization kinds; repeatable. Default: Q4_K_M",
    )
    parser.add_argument(
        "--imatrix",
        default=None,
        help="Path to an imatrix.dat; also protects embedding/output tensors at Q8_0",
    )
    parser.add_argument("--skip-convert", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    quant_kinds = args.quant or ["Q4_K_M"]

    quantize_exe = llama_exe("llama-quantize", args.llama_bin)

    # Path(...).name, not split("/"), so a Windows path with backslashes names the
    # artifacts the same way a Hub id does.
    stem = Path(args.model).name.lower()
    f16_path = out_dir / f"{stem}-f16.gguf"

    if not args.skip_convert:
        model_dir = snapshot(args.model, out_dir)
        convert = ensure_convert_script(Path(args.llama_src), args.llama_tag)
        run([sys.executable, str(convert), str(model_dir),
             "--outfile", str(f16_path), "--outtype", "f16"])

    if not f16_path.exists():
        print(f"missing {f16_path}", file=sys.stderr)
        return 1

    imatrix = Path(args.imatrix) if args.imatrix else None
    # The suffix keeps the two rungs as separate artifacts. Without it an imatrix build
    # silently overwrites the plain one, and a results row can no longer be traced to
    # the file it was measured on.
    suffix = "-imatrix" if imatrix is not None else ""
    for kind in quant_kinds:
        target = out_dir / f"{stem}-{kind.lower()}{suffix}.gguf"
        run([str(quantize_exe), *quantize_flags(kind, imatrix), str(f16_path), str(target), kind])

    print("\nArtifacts:")
    for path in sorted(out_dir.glob(f"{stem}*.gguf")):
        print(f"  {path.name:<44} {path.stat().st_size / 1e6:>8.0f} MB")
    # ASCII only: the default Windows console encoding (cp1252) cannot encode dashes.
    print("\nRecord these sizes in ml/eval/results.md; estimates run low.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
