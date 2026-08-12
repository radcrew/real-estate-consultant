# `backend/ml`

Offline model work for intake criteria extraction: evaluation, data generation, LoRA
training, quantization and serving recipes. **Nothing here runs inside the API.**

`ml/eval/results.md` is the record of what every model scored and why — read it before
changing anything here, since most of what follows exists because of a number in it.

## The pipeline, end to end

Each step's output is the next step's input, and every one of them is re-runnable from
scratch. Nothing in `.local/` is precious.

```
questions table (DB)
  └─ ml.eval.dump_questions ──→ ml/eval/questions.json      the questionnaire, generated
       └─ ml.data.make_phrasings ──→ property_type_phrasings.json   how clients say each type
            └─ ml.data.generate ──→ train.jsonl + validation.jsonl
                 └─ train/train.ipynb (Colab GPU)  or  ml.train.train_lora (CPU)
                      └─ ml.train.merge ──→ full weights
                           └─ ml.quantize.build_gguf ──→ F16 + Q4_K_M GGUFs
                                └─ ml.serve.serve_local ──→ llama-server on :8080
                                     └─ ml.eval.run ──→ results/<label>.json + a table row
```

Steps 1 and 2 only need re-running when the questionnaire changes. Steps 3 onward are the
loop you actually iterate on.

## Layout

```
ml/
  eval/       # dataset, questions, metrics, runner, results table
  data/       # phrasing and training-set generation; generated JSONL gitignored
  train/      # LoRA config, CPU entry point, and the Colab notebook
  quantize/   # fetch, convert and quantize into GGUFs
  serve/      # llama-server flags
```

Binaries, weights and GGUFs live in `<repo>/.local/`, which is gitignored. Nothing
multi-gigabyte belongs in this tree — `ml/quantize` rebuilds all of it. Paths are resolved
in one place, `ml/paths.py`; no module recomputes the repo root or searches for a
llama.cpp binary on its own.

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
2. **Model artifacts** — `.local/models/`, produced by the scripts below.

The conversion and training dependencies are an optional extra, never in
`requirements.txt`, because Vercel installs from that file and anything in it ships:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU build, not CUDA
pip install -e ".[ml]"
```

---

## 1. The questionnaire is generated, not written

```bash
python -m ml.eval.dump_questions        # overwrites ml/eval/questions.json from the DB
```

Both the harness and the data generator read `ml/eval/questions.json`. It used to be
hand-written, and it drifted from the database on the first commit and stayed wrong for
the life of the branch: it described **six** questions where the `questions` table has held
**four** since 2026-04-21, and gave them plain-string options where the real rows use
`{"label": ..., "value": ...}` dicts.

Nothing caught it. Every eval turn and every training example was built against a
questionnaire that does not exist, `where_criteria` never filtered on the two extra
fields, and the guard that validates answers against configured choices silently matched
nothing because it only understood the string form.

So: **never edit this file by hand.** Change the questionnaire in the database, re-run the
dump, then rebuild `dataset.jsonl` and `train.jsonl` — gold keys, gold values and
`next_question_key` are all keyed to it. That is a new dataset revision, and rows from the
old questionnaire are not comparable to rows from the new one.

The four live questions, in order: `property_type` (multi-select), `location`, `price`,
`size_sqft`. `ml/data/generate.py` raises rather than skipping if the questionnaire gains
a key it has no renderer for — silently omitting one would ship a set that never teaches
the new field, and the shortfall would look like ordinary deduplication loss.

## 2. Property-type phrasings

```bash
python -m ml.data.make_phrasings --model qwen/qwen-2.5-7b-instruct
```

Writes `ml/data/property_type_phrasings.json`, which is **gitignored — a build artifact,
regenerated rather than edited.**

The generator renders the option word itself half the time. Without this file it would
render it *every* time, so no training message would ever contain a word differing from
its gold, and the most reinforced rule in the set would be *copy the noun you see*. That
is exactly the failure it was built to fix: the tuned model echoed "warehouse" or "shop"
into `property_type`, the value was not a configured option, `drop_unconfigured_choices`
dropped it, and the field came back unanswered.

**Use a model that knows the mappings.** Each candidate is validated by asking the same
model to map it back, so a proposer that is wrong will also validate itself as right. The
0.5B scores 3–4 of 6 on that probe — it answers `factory → Office` — and would generate
wrong pairs and confirm them. The 7B mapped all six correctly.

A candidate claimed by two options is dropped, as is any candidate that is itself an
option word: both would put a wrong label on a training example.

## 3. Generating training data

Regenerate, then check the file before you train on it:

```bash
cd backend
python -m ml.data.generate --count 2500
python -c "
import json,collections
c=collections.Counter(); keys=set()
for l in open('ml/data/train.jsonl',encoding='utf-8'):
    d=json.loads(l); c[d['shape']]+=1
    keys |= set(json.loads(d['messages'][1]['content']))
assert 'pending_question' in keys, 'prompt field missing'
assert {'correction','pending-answer'} <= set(c), f'missing shapes: {sorted(c)}'
print('ok:', dict(c))
"
```

The two assertions catch different staleness, and neither substitutes for the other. v4
trained on a set generated before `pending_question` existed and the notebook's guard
passed, because it read only the **target** — where a stale row and a current row look
identical. A field the prompt carries has to be checked against the prompt, and a shape
against the shape counts. Run this before uploading to Colab: `train/train.ipynb` cell 2
repeats both checks, but by then a failure costs a browser round trip.

`cd backend` is load-bearing. `generate.py` writes through `ml/paths.py` and lands in the
right place from anywhere, but the check opens `ml/data/train.jsonl` as a relative path
and finds it only from `backend/`.

Its counts are lower than the generator's own shape mix below and should be: the check
reads `train.jsonl` alone, the generator reports across both files. `multi 520` against
`multi 571` is the 90/10 split, not a discrepancy.

Other useful forms:

```bash
python -m ml.data.generate                  # 2500 is the default anyway
python -m ml.data.generate --count 4000 --seed 23
```

Writes `ml/data/train.jsonl` and `ml/data/validation.jsonl`, both gitignored, split by
`--val-fraction` (0.1). The names matter: `ml/paths.py` calls the second one
`validation.jsonl` and nothing writes `val.jsonl`.

Labels are correct by construction: a criteria dict is chosen first, rendered into natural
language, and kept as gold — there is no teacher to be wrong. Prompts come from
`build_intake_messages`, the function production calls, so the training text cannot drift
from what the model sees at serving time. That is also how `pending_question` reached the
training set without anyone editing a template.

### What a run currently produces

```
wrote  2250 -> ml/data/train.jsonl
wrote   250 -> ml/data/validation.jsonl

shape mix:
  multi 571   single 463   skip 459   correction 249   pending-answer 218
  answer-and-skip 175   carried-skip 156   noise 121   complete 88

examples with empty extracted: 671 (26.8%)

rejected:
  duplicate                  273
  collides with eval set      75
```

Nine shapes, each teaching one behaviour:

| Shape | What it teaches |
|---|---|
| `single` / `multi` | Extract one field, or several from one sentence |
| `skip` | A refusal is not noise — the field is *declined*, not unmentioned |
| `answer-and-skip` | Answering and refusing in one message are not mutually exclusive |
| `carried-skip` | A field skipped earlier stays skipped |
| `noise` | Greetings and questions extract nothing |
| `complete` | A confirmation adds no criteria |
| `correction` | Restating an answered field replaces it, marked (*"actually…"*) or bare |
| `pending-answer` | A bare value belongs to the question that was just asked |

### The set teaches precision, not recall

The P2 baseline put the stock 0.5B at precision 0.15 with recall 1.0 — it already finds
every field; what it cannot do is stop. So about a quarter of examples have empty
`extracted`, the average example names fewer than two fields, and no example ever lists a
key in both `extracted` and `skipped_fields`. `tests/ml/test_data_generate.py` fails if
any of those drift.

### Gold conventions

These are not arbitrary, and the eval scores against the same ones. Getting them wrong in
either place marks a correctly-trained model wrong:

* A **bare budget is a ceiling**: `half a million` → `{"max": 500000}`.
* A **bare size is exact**: `10,000 sqft` → `{"min": 10000, "max": 10000}`. v3 generated
  max-only for both, so answering the size question with `32` trained a 32 sqft ceiling
  and every later correction stacked against it.
* A figure in **square yards golds square feet**: `1,500 yards` → `13500`. The only unit
  in the set where the stated figure and the gold figure differ, so it is the only place
  the model must convert rather than copy.

### Ambiguity is taught, not removed

Several tokens carry two meanings, and in each case both stay in the set so context has to
do the work. Removing either sense would only move the failure:

| Token | Sense A | Sense B |
|---|---|---|
| `SF` | square feet, after a figure | San Francisco, as a place |
| `floor` | a lower bound (`a floor of $400k`) | a storey (`ground floor only`), extracted into nothing |
| `ground` | the `land` property type | half of `ground floor` |
| `yard` | square yards, after a figure | `fenced yard`, a requirement in no field |

The ratio is the whole game. `ground` reached ~8 messages against 18 for `ground floor`,
so the token's own statistics said *ignore me*, and it was dropped in production;
ambiguous phrasings are now weighted 8×. That weight is measured rather than picked — at
4× five seeds ran 16v19, 18v16, 25v7, 11v14, 17v16, so which sense won came down to the
draw.

### Why the refusal phrasings are so varied

A refusal and a piece of noise both produce empty `extracted`. The only thing separating
them is how the message is worded, so that vocabulary is the entire training signal for
skip detection.

The first pass used 14 refusal strings and the model learned the strings rather than the
concept: it missed four of ten eval refusals, and in each case returned empty `extracted`
and then **re-asked the very field being refused** — it had classified the refusal as
noise. The list is now ~60 phrasings across registers (blunt, polite, deferring,
indifferent), and `skip` is over-weighted because refusal phrasings collapse under
deduplication far harder than extraction phrasings do.

### Nothing the eval scores may reach training

Two guards, and they have failed in different ways:

* Any generated message whose wording matches an eval turn is dropped. The key is
  `user_input` **alone**, not the `(input, criteria)` pair: for a skip or noise turn the
  wording *is* the whole signal, and keying on the pair let r2 ship with 9 of 25 skip turns
  reusing a phrase list.
* `collision_key` folds case and the punctuation `_rough_up` adds before comparing. The
  raw comparison ran *before* roughening, so `that's everything` reached the r6 training
  set four ways — upper-cased, sentence-cased, with a full stop, with `!!` — while the
  generator reported it held out. A blank message is exempt: the empty and whitespace eval
  turns score a behaviour, not a phrasing, and withholding them would leave that behaviour
  untaught.

The generated *vocabulary* is held out too, in the categories that exist to measure
generalisation. `TestSynonymEvalSeparation` fails if a `property-synonym` turn reuses a
phrasing from the file above; `TestBoundWordingEvalSeparation` fails if a `bound-direction`
turn is an instance of a comparator template. Two phrasings added during the bound fix were
a turn verbatim, and one of those turns already scored correct — a guaranteed pass bought
at the cost of the only honest reading of the category.

### Two limits worth knowing

Phrasings are templated, so the set is stylistically narrower than real user input — the
eval set is hand-written prose precisely so it does not reward overfitting to these
templates. And the fixed phrase lists still deduplicate, so raising `--count` past a few
thousand mostly adds extraction examples rather than negative ones.

## 4. Training the adapter

### On Colab (what v4 used)

`ml/train/train.ipynb`. Upload `train.jsonl` and `validation.jsonl`, run top to bottom,
download `lora-intake-v4.zip` and unzip into `.local/models/`. LoRA r=16, alpha=32,
dropout 0.05, all seven projections, `MAX_LEN` 1088, batch 2 × grad-accum 4, bf16,
gradient checkpointing. Roughly 17 MB of adapter.

Cell 2 is a staleness guard, and it earned its place: the first v4 run trained on a
dataset generated before `pending_question` existed, and the guard passed, because it
only inspected the target. **A field the prompt carries has to be checked against the
prompt, and a shape against the shape counts** — it now checks all three. The training
cell adds a second gate, asserting the loss mask lands between 2% and 15% before the
model is loaded, so a bad mask costs seconds rather than a GPU hour.

### On CPU

```bash
python -m ml.train.train_lora --smoke     # a handful of steps, verifies the pipeline
python -m ml.train.train_lora             # the real run
```

Loss is on completion tokens only — the prompt is masked to `-100`. Measured on the
current set: rows average **916 tokens, of which the completion is ~25**, so **2.7% of
tokens are supervised**. Training on the rest would spend the gradient teaching the model
to recite a schema it is handed at inference time anyway.

The chat template comes from the tokenizer, never hand-rolled — hand-written ChatML
markers produce a model that scores fine in a notebook and misbehaves behind
`llama-server`. The encoder asserts the prompt is a strict prefix of the full sequence and
drops any example where it is not, because a mask in the wrong place trains on nothing
useful and fails silently.

`bf16` is used on CUDA and `fp32` on CPU. bf16 is right on a GPU; a CPU with neither
AVX512-BF16 nor AMX emulates it, which costs speed rather than saving it.

**Cost.** Last measured on an i7-10750H (6 physical cores) at **~12.1 s/example**, batch 1
× grad-accum 8, when rows averaged 718 tokens. Rows now average 916, and attention is
quadratic in length, so treat that figure as a floor rather than an estimate — and
re-measure after any prompt change, since it tracks sequence length rather than the model.

| Path | Time | Note |
|---|---|---|
| CPU, full set, 2 epochs | ~12 h+ | Run it overnight; nothing else needs the machine |
| CPU, 600 examples, 1 epoch | ~2 h+ | Enough to see whether the adapter moves the metrics |
| CPU, under ~600 examples | — | Not worth it; the effect lands inside the eval's noise |

Epoch count is not a free parameter to vary alongside a data change: v3 trained 2 epochs
and the notebook currently sets 1, so a 1-epoch run on new data confounds *new data* with
*half the training*.

## 5. Merging and quantizing

```bash
python -m ml.train.merge --adapter .local/models/lora-intake-v4 \
  --out .local/models/Qwen2.5-0.5B-Instruct-intake-v4
python -m ml.quantize.build_gguf --model .local/models/Qwen2.5-0.5B-Instruct-intake-v4
```

`convert_hf_to_gguf.py` reads full weights, not adapters, so the merge is required. The
tokenizer travels with the weights — conversion reads it from the same directory, and a
mismatched one produces a model that decodes to noise.

Order matters: **evaluate the merged F16 before quantizing.** That is what makes a later
regression attributable to one step or the other. Both artifacts are kept for the same
reason — measuring the two together makes a regression unattributable to either.

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

Two caveats, both measured. On this model `llama-quantize` reported *144 of 290 tensors
required fallback quantization*, because the 0.5B's 896-wide tensors do not divide evenly
for every K-quant — "Q4_K_M" here is really ~6.35 bits per weight, so expect the imatrix to
buy less than it would on a model whose shapes cooperate. And it did not pay: results.md
has the imatrix build at 0.901 against 0.935, for an hour per build. **Ship the plain
Q4_K_M.**

## 6. Serving locally

```bash
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m.gguf
```

Threads default to physical cores, `--parallel` to 1, and prefix caching is on. Those
choices decide what a latency number means, which is why they are in a script rather than
in someone's shell history. See `ml/serve/README.md` for the production deployment.

## 7. Running the eval

From `backend/`, with `.env` present (the settings module loads it at import):

```bash
# A local llama-server, no credits and no cloud involved
python -m ml.eval.run --label 0.5b-lora-v4-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m

# The incumbent, on the hosted router
python -m ml.eval.run --label 7b-router --model "Qwen/Qwen2.5-7B-Instruct"

# The held-out split, which never enters training
python -m ml.eval.run --label 0.5b-lora-v4-q4km-holdout --split holdout ...
```

Results are written to `ml/eval/results/<label>.json` — per-turn scores plus the raw model
output for every turn, which is where failure modes are actually visible. The command
prints a markdown row to paste into `ml/eval/results.md`.

**Give every run a distinct label.** The file is `results/<label>.json` and a rebuild
overwrites it silently, so a re-trained model reusing an old label destroys the row it was
meant to be compared against.

| Flag | Why |
|---|---|
| `--split holdout` | Score the slice reserved from training |
| `--category bound-direction` | Isolate one behaviour while iterating |
| `--concurrency N` | Leave at 1 for CPU serving; parallel requests contend for cores |
| `--limit N` | Smoke-test the harness without spending a full pass |
| `--duplicate-schema` | Re-add the provider's schema copy, as intake sent before P1 |
| `--no-json-mode` | For endpoints that reject `response_format` |
| `--no-next-question` | Score next-question accuracy as n/a. Always pass this: the backend picks the question from `questions.json`, so nothing the model writes there is used |

### Reading the numbers

Field precision/recall/F1 ask *did it name the right keys*; **value accuracy** asks *did it
get the values right*, and the gap between them is where this model actually fails.
`bound-direction` has run field F1 1.000 with value accuracy 0.375 — right field, right
figure, wrong direction. A category table with only F1 in it hides that completely.

Per-category numbers on 5–8 turns are coarse by construction: one turn is 0.125. Treat a
single category's movement as a lead to investigate, not a result, and read the per-turn
`raw_output` before believing either.

### Why the harness imports from `app`

Prompts come from `build_intake_messages` and decode settings from
`INTAKE_PARSE_TEMPERATURE` / `INTAKE_PARSE_MAX_TOKENS`, both in
`app.llm.intake.service`. The duplicate schema copy comes from
`structured_output_messages` in `app.llm.providers.huggingface`.

None of it is restated here. A prompt change in the backend changes what the harness
scores on the next run, which is the only way to stop the two drifting apart.

The one thing the harness deliberately does **not** reuse is the provider's reply
handling: it reads `choices[0].message.content` raw, with no fence-stripping and no
retry, because raw JSON validity is one of the numbers being measured.

## Adding turns to the eval set

`ml/eval/dataset.jsonl`, one JSON object per line. Currently 129 turns across 12
categories, 92 dev / 37 holdout:

```json
{"id": "...", "category": "...", "split": "dev|holdout",
 "user_input": "...", "current_criteria": {},
 "gold": {"extracted": {}, "skipped_fields": [], "next_question_key": null}}
```

Follow the labelling conventions in `eval/results.md`, and use the gold conventions above
rather than inventing new ones — scoring against a different convention marks a correctly
trained model wrong.

Two things to check before adding a turn, both of which have gone wrong before:

* **Does the turn actually test what it claims?** A `pending-answer` turn is only
  meaningful if its `current_criteria` really produce the pending question you have in
  mind. Assert it against `pending_question_key` rather than reasoning it out.
* **Is the wording one the generator emits?** If so the turn measures recall of a list,
  not generalisation. This project has made that mistake three times — 14 refusal strings,
  4 comparator phrasings, then 2 bound wordings.

Adding or changing turns starts a new dataset revision. Rows scored against different
revisions are not comparable and must not share a table.

## After a fine-tune: from adapter zip to a results row

The steps below are one pass, in order, with v5 as the worked example. Everything before
this point produced an adapter; nothing after it changes the weights, so a mistake here
costs a re-run rather than a re-train.

Unzip into `.local/models/`, then confirm the run before spending an hour on it:

```bash
cd backend
python -c "
import json; s=json.load(open('../.local/models/lora-intake-v5/checkpoint-338/trainer_state.json'))
print(s['epoch'], s['global_step'], s['num_train_epochs'])"
```

`global_step` × batch × grad-accum has to equal the rows in the `train.jsonl` you uploaded,
times the epochs. 338 × 2 × 4 = 2704 against 2700 rows is one epoch; anything else means
the notebook and the dataset disagree and the row you are about to measure is not the run
you think it is. Check `adapter_config.json` against the previous version at the same
time — `r`, `lora_alpha`, `lora_dropout`, `target_modules`. **A hyperparameter that moved
alongside the data confounds the comparison**, which is the same trap the epoch count set
in §4.

### 0. Re-score the incumbent first, if this dataset revision has never been scored

```bash
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m.gguf
python -m ml.eval.run --label 0.5b-lora-v4-q4km-r7 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m
```

Rows from different revisions do not share a table, so a new model scored on a fresh
revision has nothing to be compared against and the whole run answers no question. This
costs one eval pass against a GGUF that already exists. v3 was re-scored for r6 and v4 for
r7 for exactly this reason; the label carries the revision suffix so it cannot be mistaken
for the original row.

### 1. Merge, convert, quantize

```bash
python -m ml.train.merge --adapter ../.local/models/lora-intake-v5 \
  --out ../.local/models/Qwen2.5-0.5B-Instruct-intake-v5
python -m ml.quantize.build_gguf --model ../.local/models/Qwen2.5-0.5B-Instruct-intake-v5
```

Paths are ordinary relative paths resolved against the cwd, and every command in this file
runs from `backend/` — hence `../.local`, not `.local`. The merged directory name decides
the GGUF names, so `Qwen2.5-0.5B-Instruct-intake-v5` is what produces
`qwen2.5-0.5b-instruct-intake-v5-{f16,q4_k_m}.gguf` and the eval `--model` ids below.

**No `--imatrix`.** Measured at F1 0.901 against 0.935 for an hour per build; see §5.
Record the two artifact sizes and the `quant size` / fallback-tensor lines in `results.md`.

### 2. Score F16, then Q4_K_M, one server at a time

```bash
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-intake-v5-f16.gguf
python -m ml.eval.run --label 0.5b-lora-v5-f16 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v5-f16

# stop the first server before starting the second — same port, and the p50/p95
# columns are only meaningful if nothing else is contending for the cores
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-intake-v5-q4_k_m.gguf
python -m ml.eval.run --label 0.5b-lora-v5-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v5-q4_k_m
```

F16 first: with both rows in hand, a v5 failure that F16 also fails is training and one it
passes is quantization damage. Three of v5's four regressions against v4 were the latter,
and there is no way to say that from the Q4 row alone.

Poll `/v1/models` rather than `/health` when scripting the wait — it names the model being
served, so you cannot start an eval against the previous GGUF still shutting down.

**Every run needs a label no `results/` file already owns.** The file is
`results/<label>.json` and a rebuild overwrites it silently.

### 3. Read the turns before writing the row

The summary table hides the two things worth knowing. Diff the per-turn outcomes against
the baseline run rather than reading category cells:

```bash
python - <<'PY'
import json
def turns(lab):
    return {t['turn_id']: t for t in
            json.load(open(f'ml/eval/results/{lab}.json', encoding='utf-8'))['turns']}
def ok(t):
    return (t['field_fp'] == 0 and t['field_fn'] == 0 and t['skip_fp'] == 0
            and t['skip_fn'] == 0
            and (t['value_compared'] == 0 or t['value_correct'] == t['value_compared']))
old, new = turns('0.5b-lora-v4-q4km-r7'), turns('0.5b-lora-v5-q4km')
print('regressed:', [i for i in new if ok(old[i]) and not ok(new[i])])
print('fixed    :', len([i for i in new if not ok(old[i]) and ok(new[i])]))
PY
```

A category can hold flat while turns move in both directions underneath it, and per-category
numbers on 5–8 turns are coarse by construction — one turn is 0.125 or 0.200. Read
`raw_output` for every regression and for every turn the training change was aimed at.
`value_compared == 0` means the turn golds no values, so it must not count as a value miss.

### 4. Record it

A new revision starts a new table in `results.md`, with the serving flags, the three
commands verbatim, and a statement of what changed between the models and what did not.
"Only `train.jsonl` changed" is the sentence that makes every number in the table
attributable; if it is not true, say what else moved.
