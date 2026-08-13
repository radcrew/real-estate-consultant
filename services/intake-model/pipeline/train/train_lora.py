"""LoRA fine-tune of Qwen2.5-0.5B-Instruct for intake criteria extraction.

    cd services/intake-model
    python -m pipeline.train.train_lora --smoke          # a few steps, verifies the pipeline
    python -m pipeline.train.train_lora                  # the real run

A one-off offline job, not part of the running app. Produces a LoRA adapter under
``<repo>/.local/models/lora-intake/``; ``pipeline.train.merge`` folds it into the base weights
so ``pipeline.quantize.build_gguf`` can convert the result.

Two decisions carry most of the weight here:

**Loss on completion tokens only.** Prompt tokens are masked to -100. The prompt is ~929
tokens of schema and rules, the completion ~31; training on both would spend 97% of the
gradient teaching the model to recite a schema it is already given at inference time.

**Prompts come from the training file, which came from ``build_intake_messages``.** The
chat template is applied by the tokenizer, never hand-rolled — hand-written ChatML markers
produce a model that scores fine in a notebook and misbehaves behind ``llama-server``.

On CPU this is hours, not minutes, and that is expected for a job run a handful of times.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

from pipeline.paths import MODELS_DIR, TRAIN_PATH, VAL_PATH

DEFAULT_BASE = MODELS_DIR / "Qwen2.5-0.5B-Instruct"
DEFAULT_OUT = MODELS_DIR / "lora-intake"

# All attention and MLP projections, per the plan. Attention alone underfits the value
# formatting; the MLP projections are where "omit this property" lives.
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]

IGNORE_INDEX = -100


@dataclass
class Encoded:
    input_ids: list[int]
    labels: list[int]


class IntakeDataset(Dataset):
    """Chat records with the prompt masked out of the loss."""

    def __init__(self, path: Path, tokenizer, max_len: int) -> None:
        self.rows: list[Encoded] = []
        self.truncated = 0
        self.prefix_mismatches = 0

        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            messages = json.loads(line)["messages"]
            encoded = self._encode(messages, tokenizer, max_len)
            if encoded is not None:
                self.rows.append(encoded)

    def _ids(self, tokenizer, messages, *, generation_prompt: bool) -> list[int]:
        out = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=generation_prompt,
            return_dict=True,
        )
        ids = out["input_ids"]
        if ids and isinstance(ids[0], list):
            ids = ids[0]
        return list(ids)

    def _encode(self, messages: list[dict[str, str]], tokenizer, max_len: int) -> Encoded | None:
        full = self._ids(tokenizer, messages, generation_prompt=False)
        prompt = self._ids(tokenizer, messages[:-1], generation_prompt=True)

        # The prompt must be a strict prefix of the full sequence, or the mask would cut
        # the completion in the wrong place and train on nothing useful.
        if full[: len(prompt)] != prompt or len(prompt) >= len(full):
            self.prefix_mismatches += 1
            return None

        if len(full) > max_len:
            self.truncated += 1
            full = full[:max_len]
            if len(prompt) >= len(full):
                return None

        labels = [IGNORE_INDEX] * len(prompt) + full[len(prompt):]
        return Encoded(input_ids=full, labels=labels)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        row = self.rows[index]
        return {"input_ids": row.input_ids, "labels": row.labels}


@dataclass
class PadCollator:
    """Right-pad a batch; label padding is IGNORE_INDEX so it never enters the loss."""

    pad_token_id: int

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, torch.Tensor]:
        width = max(len(f["input_ids"]) for f in features)
        input_ids, labels, attention = [], [], []
        for feature in features:
            ids = feature["input_ids"]
            lab = feature["labels"]
            pad = width - len(ids)
            input_ids.append(ids + [self.pad_token_id] * pad)
            labels.append(lab + [IGNORE_INDEX] * pad)
            attention.append([1] * len(ids) + [0] * pad)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(attention, dtype=torch.long),
        }


def pick_precision() -> dict[str, Any]:
    """bf16 on CUDA; fp32 on CPU.

    The plan specifies bf16, which is right on a GPU. On a CPU without AVX512-BF16 or AMX
    the dtype is emulated, so it costs speed instead of saving it. fp32 is the honest
    choice here, and a 0.5B adapter does not need the memory saving.
    """
    if torch.cuda.is_available():
        return {"bf16": True}
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=str(DEFAULT_BASE))
    parser.add_argument("--train", default=str(TRAIN_PATH))
    parser.add_argument("--val", default=str(VAL_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    # p99 total length is 1014 tokens on the current set; 1088 clears the max with room.
    parser.add_argument("--max-len", type=int, default=1088)
    parser.add_argument("--rank", type=int, default=8)
    parser.add_argument("--alpha", type=int, default=16)
    parser.add_argument("--dropout", type=float, default=0.05)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Cap the training set. CPU runs cost ~24.5s/example, so this is the dial "
             "between a 4-hour probe and a 24-hour full run",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a handful of steps on a slice, to verify the pipeline before the real run",
    )
    args = parser.parse_args()

    if args.threads:
        torch.set_num_threads(args.threads)

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_set = IntakeDataset(Path(args.train), tokenizer, args.max_len)
    val_set = IntakeDataset(Path(args.val), tokenizer, args.max_len)
    if args.max_examples:
        train_set.rows = train_set.rows[: args.max_examples]
    print(f"train {len(train_set)} | val {len(val_set)}")
    if train_set.truncated or val_set.truncated:
        print(f"WARNING truncated {train_set.truncated + val_set.truncated} examples "
              f"at max_len={args.max_len}")
    if train_set.prefix_mismatches or val_set.prefix_mismatches:
        print(f"WARNING dropped {train_set.prefix_mismatches + val_set.prefix_mismatches} "
              "examples whose prompt was not a prefix of the full sequence")
    if not train_set.rows:
        print("no usable training examples")
        return 1

    supervised = sum(sum(1 for x in r.labels if x != IGNORE_INDEX) for r in train_set.rows)
    total = sum(len(r.labels) for r in train_set.rows)
    print(f"supervised tokens: {supervised}/{total} ({supervised / total:.1%}) "
          "- the rest is the prompt, masked out")

    model = AutoModelForCausalLM.from_pretrained(args.base, dtype=torch.float32)
    model.config.use_cache = False
    # Do not resize or retrain the embedding matrix: the vocabulary is unchanged, and a
    # resized matrix breaks GGUF conversion downstream.
    lora = LoraConfig(
        r=args.rank,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=TARGET_MODULES,
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    out_dir = Path(args.out)
    training_args = TrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        num_train_epochs=args.epochs if not args.smoke else 1,
        max_steps=6 if args.smoke else -1,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=args.warmup_ratio,
        logging_steps=1 if args.smoke else 10,
        eval_strategy="steps",
        eval_steps=3 if args.smoke else 100,
        save_strategy="no" if args.smoke else "epoch",
        save_total_limit=2,
        report_to=[],
        seed=args.seed,
        remove_unused_columns=False,
        **pick_precision(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_set if not args.smoke else torch.utils.data.Subset(
            train_set, range(min(48, len(train_set)))),
        eval_dataset=val_set if not args.smoke else torch.utils.data.Subset(
            val_set, range(min(8, len(val_set)))),
        data_collator=PadCollator(pad_token_id=tokenizer.pad_token_id),
    )

    trainer.train()

    if args.smoke:
        print("\nsmoke run complete; nothing saved")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print(f"\nadapter saved to {out_dir}")
    print(
        "Next: python -m pipeline.train.merge, "
        "then pipeline.quantize.build_gguf on the merged dir."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
