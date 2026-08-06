"""Fold a LoRA adapter into the base weights, producing a model GGUF conversion can read.

    cd backend
    python -m ml.train.merge

``convert_hf_to_gguf.py`` reads full weights, not adapters, so this step is required
before quantization. It is also the point where the plan's order matters:

    train -> merge -> evaluate the merged bf16 -> convert -> quantize -> evaluate again

Evaluating the merged model *before* quantizing is what makes a later regression
attributable to one step or the other.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS = REPO_ROOT / ".local" / "models"
DEFAULT_BASE = MODELS / "Qwen2.5-0.5B-Instruct"
DEFAULT_ADAPTER = MODELS / "lora-intake"
DEFAULT_OUT = MODELS / "Qwen2.5-0.5B-Instruct-intake"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=str(DEFAULT_BASE))
    parser.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    adapter = Path(args.adapter)
    if not adapter.exists():
        print(f"no adapter at {adapter}; run ml.train.train_lora first")
        return 1

    print(f"base    {args.base}")
    print(f"adapter {adapter}")
    model = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.float32)
    model = PeftModel.from_pretrained(model, str(adapter))
    model = model.merge_and_unload()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out))
    # The tokenizer must travel with the weights: conversion reads it from the same
    # directory, and a mismatched one produces a model that decodes to noise.
    AutoTokenizer.from_pretrained(args.base).save_pretrained(str(out))
    print(f"\nmerged -> {out}")
    print(f"Next: python -m ml.quantize.build_gguf --model {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
