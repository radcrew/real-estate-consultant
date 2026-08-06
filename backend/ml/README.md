# `backend/ml`

Offline model work for intake criteria extraction: evaluation, data generation, LoRA
training, quantization and serving recipes. **Nothing here runs inside the API.**

See `INTAKE_MODEL_FINETUNE_PLAN.md` at the repo root for what this is for and the gate
that decides whether it ships.

## Layout

```
ml/
  eval/       # dataset, questions, metrics, runner, results table   ← P0
  quantize/   # fetch, convert and quantize into GGUFs               ← P2, P6
  serve/      # llama-server flags                                   ← P2, P8
  data/       # training-set generation; generated JSONL gitignored  ← P4
  train/      # LoRA config and entry point                          ← P5
```

Binaries, weights and GGUFs live in `<repo>/.local/`, which is gitignored. Nothing
multi-gigabyte belongs in this tree — `ml/quantize` rebuilds all of it.

`ml/` is listed in `.vercelignore`, so none of it is uploaded to the serverless
function. It lives under `backend/` anyway so the harness can
`from app.llm.intake.service import build_intake_messages` without a `sys.path` hack,
and so one venv covers both.

Tests live in `backend/tests/ml/`, because `testpaths = ["tests"]` means pytest never
collects anything under `ml/`.

Weights, GGUFs and generated datasets go to the Hub or object storage, never into git.

## Local setup

Two things live outside the venv, both in `<repo>/.local/`:

1. **llama.cpp binaries** — download the release zip for your platform from
   `ggml-org/llama.cpp` and unzip into `.local/bin/`. On an AVX2 CPU with no AVX-512,
   the plain `bin-win-cpu-x64` build is correct; it dispatches at runtime.
2. **Model artifacts** — `.local/models/`, produced by the script below.

The conversion and training dependencies are an optional extra, never in
`requirements.txt`, because Vercel installs from that file and anything in it ships:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU build, not CUDA
pip install -e ".[ml]"
```

## Building the GGUFs

```bash
python -m ml.quantize.build_gguf --model Qwen/Qwen2.5-0.5B-Instruct
```

Downloads the snapshot, converts to F16, and quantizes to Q4_K_M. Both artifacts are
kept on purpose: F16 against Q4_K_M isolates what quantization alone costs, before
fine-tuning is in the picture. Measuring the two together makes a regression
unattributable to either.

At P6, add `--imatrix path/to/imatrix.dat`, which also protects the embedding and output
tensors at Q8_0. It is off for the stock baseline so that row measures plain Q4_K_M.

### Importance matrix

```bash
python -m ml.quantize.make_imatrix --gguf qwen2.5-0.5b-instruct-intake-f16.gguf
python -m ml.quantize.build_gguf --model <merged-dir> --imatrix .local/models/imatrix.dat
```

`llama-quantize` has to decide which weights tolerate 4 bits. Unaided it uses a generic
notion of importance; given an imatrix it uses activations measured on text you supply.
Calibrating on intake prompts is exactly the case where that pays, because the model only
ever sees this one prompt shape in production.

Calibration is drawn from the **training** split. Using the eval split would launder eval
information into the artifact you then score.

One caveat measured at P2: on this model `llama-quantize` reported *144 of 290 tensors
required fallback quantization*, because the 0.5B's 896-wide tensors do not divide evenly
for every K-quant. "Q4_K_M" here is really ~6.35 bits per weight, so expect the imatrix to
buy less than it would on a model whose shapes cooperate.

## Serving locally

```bash
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-q4_k_m.gguf
```

Threads default to physical cores, `--parallel` to 1, and prefix caching is on. Those
choices decide what a latency number means, which is why they are in a script rather
than in someone's shell history.

## Generating training data

```bash
python -m ml.data.generate --count 2000
```

Writes `ml/data/train.jsonl` and `val.jsonl`, both gitignored. Labels are correct by
construction: a criteria dict is chosen first, rendered into natural language, and kept
as gold — there is no teacher to be wrong.

**The set is built to teach precision, not recall.** The P2 baseline put the stock 0.5B
at precision 0.15 with recall 1.0, so it already finds every field; what it cannot do is
stop. About a third of examples therefore have empty `extracted` (noise, greetings, pure
skips, confirmations), the average example names fewer than two fields, and no example
ever lists a key in both `extracted` and `skipped_fields`.

Every row is validated before it is written, and any row whose `(user_input,
current_criteria)` matches the eval set is dropped, so training never contains a turn we
score on. Prompts come from `build_intake_messages`, so the training text is what the
model will see at serving time.

Two limits worth knowing. Phrasings are templated, so the set is stylistically narrower
than real user input — the eval set is hand-written prose precisely so it does not
reward overfitting to these templates. And skip and noise inputs come from fixed phrase
lists, so they deduplicate hard; raising `--count` past a few thousand mostly adds
extraction examples rather than negative ones.

## Training the adapter

```bash
python -m ml.train.train_lora --smoke     # 6 steps, verifies the pipeline
python -m ml.train.train_lora             # the real run
python -m ml.train.merge                  # fold the adapter into the base weights
```

Loss is on completion tokens only — the prompt is masked to `-100`. On the current set
that means **3.7% of tokens are supervised**; training on the rest would spend the
gradient teaching the model to recite a schema it is handed at inference time anyway.

The chat template comes from the tokenizer. The encoder asserts the prompt is a strict
prefix of the full sequence and drops any example where it is not, because a mask in the
wrong place trains on nothing useful and fails silently.

### Cost on CPU, measured

On an i7-10750H (6 physical cores) the smoke run came in at **~196 s per optimizer step**
at batch 1 × grad-accum 8, so roughly 24.5 s per example. A full 2-epoch run over 1800
examples is about **24 hours**.

That is the number open decision 2 needs. The options, in order of how much they cost you:

| Path | Time | Note |
|---|---|---|
| Free hosted GPU notebook | minutes | A GPU you do not own, provision or pay for, used once, offline |
| CPU, full set, 2 epochs | ~24 h | Run it overnight; nothing else needs the machine |
| CPU, 600 examples, 1 epoch | ~4 h | Enough to see whether the adapter moves the metrics at all |

`bf16` is used on CUDA and `fp32` on CPU. The plan specifies bf16, which is right on a
GPU; this CPU has neither AVX512-BF16 nor AMX, so bf16 would be emulated and cost speed
rather than save it.

## Running the eval

From `backend/`, with `.env` present (the settings module loads it at import):

```bash
# The incumbent, on the hosted router
python -m ml.eval.run --label 7b-router --model "Qwen/Qwen2.5-7B-Instruct"

# A local llama-server, no credits and no cloud involved
python -m ml.eval.run --label 0.5b-q4km-local \
  --base-url http://localhost:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-q4_k_m

# The held-out split, which never enters training
python -m ml.eval.run --label 0.5b-q4km-holdout --split holdout ...
```

Results are written to `ml/eval/results/<label>.json` — per-turn scores plus the raw
model output for every turn, which is where failure modes are actually visible. The
command prints a markdown row to paste into `ml/eval/results.md`.

Useful flags:

| Flag | Why |
|---|---|
| `--split holdout` | Score the slice reserved from training |
| `--category skip` | Isolate one behaviour while iterating |
| `--concurrency N` | Leave at 1 for CPU serving; parallel requests contend for cores |
| `--duplicate-schema` | Re-add the provider's schema copy, as intake sent before P1 |
| `--no-json-mode` | For endpoints that reject `response_format` |
| `--no-next-question` | Score next-question accuracy as n/a once the key leaves the schema |

## Why the harness imports from `app`

Prompts come from `build_intake_messages` and decode settings from
`INTAKE_PARSE_TEMPERATURE` / `INTAKE_PARSE_MAX_TOKENS`, both in
`app.llm.intake.service`. The duplicate schema copy comes from
`structured_output_messages` in `app.llm.providers.huggingface`.

None of it is restated here. A prompt change in the backend changes what the harness
scores on the next run, which is the only way to stop the two drifting apart.

The one thing the harness deliberately does **not** reuse is the provider's reply
handling: it reads `choices[0].message.content` raw, with no fence-stripping and no
retry, because raw JSON validity is one of the numbers being measured.

## Adding turns to the dataset

`eval/dataset.jsonl`, one JSON object per line:

```json
{"id": "...", "category": "...", "split": "dev|holdout",
 "user_input": "...", "current_criteria": {},
 "gold": {"extracted": {}, "skipped_fields": [], "next_question_key": null}}
```

Follow the labelling conventions at the top of `eval/results.md`. Adding or changing
turns invalidates every existing row in the results table — start a new table.
