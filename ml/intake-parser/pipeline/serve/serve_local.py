"""Start ``llama-server`` with the flags the eval assumes.

    cd ml/intake-parser
    python -m pipeline.serve.serve_local --model qwen2.5-0.5b-instruct-q4_k_m.gguf

Then, in another shell:

    python -m pipeline.eval.run --label 0.5b-q4km-local \
        --base-url http://127.0.0.1:8080/v1 --api-key local \
        --model qwen2.5-0.5b-instruct-q4_k_m

The defaults here are the CPU-serving decisions from the plan, in one place so a results
row can be reproduced:

- ``-t`` is **physical** cores, not logical. Hyperthreading makes generation slower here,
  because the two threads on a core contend for the same vector units.
- ``--parallel 1``: on CPU, concurrent requests contend for those same cores. More slots
  makes each request slower rather than the system faster. Raise only to measure
  contention deliberately.
- ``--cache-reuse``: the intake prompt is a large constant prefix followed by a small
  variable payload, which is exactly the shape prefix caching wants. This is the flag
  that stops it being reprocessed on every turn.
- ``--jinja``: use the model's own chat template. Hand-rolled ChatML markers produce a
  model that scores fine in a notebook and misbehaves behind the server.

Production adds ``--api-key`` and TLS in front. This script is for localhost only and
binds to 127.0.0.1 for that reason.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from pipeline.paths import LLAMA_BIN_DIR, MODELS_DIR, llama_exe


def physical_cores() -> int:
    """Best-effort physical core count; falls back to half the logical count.

    ``-t`` is part of what makes a results row reproducible, so a wrong count is worth
    knowing about. The fallback prints rather than passing silently.
    """
    if sys.platform == "win32":
        try:
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_Processor).NumberOfCores"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return max(1, sum(int(n) for n in out.split()))
        except (subprocess.SubprocessError, OSError, ValueError) as exc:
            print(f"could not read physical core count ({exc}); halving the logical count")
    return max(1, (os.cpu_count() or 2) // 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="GGUF filename or full path")
    parser.add_argument("--models-dir", default=str(MODELS_DIR))
    parser.add_argument("--llama-bin", default=str(LLAMA_BIN_DIR))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--ctx-size", type=int, default=4096)
    parser.add_argument("--threads", type=int, default=None, help="Default: physical cores")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--cache-reuse", type=int, default=256)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--alias", default=None, help="Model id the API reports")
    args = parser.parse_args()

    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = Path(args.models_dir) / args.model
    if not model_path.exists():
        print(f"model not found: {model_path}", file=sys.stderr)
        return 1

    exe = llama_exe("llama-server", args.llama_bin)

    threads = args.threads or physical_cores()
    alias = args.alias or model_path.stem

    cmd = [
        str(exe),
        "-m", str(model_path),
        "-a", alias,
        "-c", str(args.ctx_size),
        "-t", str(threads),
        "--host", args.host,
        "--port", str(args.port),
        "--parallel", str(args.parallel),
        "--cache-reuse", str(args.cache_reuse),
        "--jinja",
    ]
    if args.api_key:
        cmd += ["--api-key", args.api_key]

    print(f"serving {model_path.name} as '{alias}' on {threads} threads")
    print(f"$ {' '.join(cmd)}\n", flush=True)
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())
