# Intake extraction: eval results

Every row is one `ml/eval/run.py` invocation. **Record the command**, because a row is
only meaningful alongside the dataset revision, the split, and whether the duplicate
schema copy and JSON mode were on.

**Rows from different `dataset.jsonl` revisions are not comparable and must not share a
table.** When the dataset changes, previous rows become historical and a new table starts.

## Dataset revisions

| Rev | Turns | Questionnaire | Notes |
|---|---|---|---|
| **r4 (current)** | 102 | **the real one** | First revision built from the live `questions` table |
| r3 | 110 | fictional | `bound-direction` added, skip turns decontaminated. Never published |
| r2 | 102 | fictional | skip 10 → 25, new `answer-and-skip` category |
| r1 | 52 | fictional | Original set |

r1's 10 skip turns meant skip recall could not resolve anything finer than 0.1, which was
useless for judging a change aimed squarely at skip detection. That is why r2 exists.

### Everything before r4 was scored against a questionnaire that does not exist

`ml/eval/questions.json` was hand-written when the harness was built and never checked
against the database. It described **six** questions; the `questions` table has held
**four** since 2026-04-21, and nothing on this branch added or removed a row. So
`listing_type` and `loading_docks` have never existed, `where_criteria` does not filter on
them, and **92 of r3's 110 turns referenced one of them**. A further 50 used property
types the questionnaire never offered.

Every r1, r2 and r3 number was therefore measured on a longer prompt with two extra
extraction targets than production has ever sent. Those rows are kept below because the
comparisons *within* a revision were internally consistent — INT4 costing nothing, v1
against v2 — but no absolute figure from them describes the shipped product.

r4 is a dump of the live table (`ml.eval.dump_questions`), with the dataset rebuilt against
it: 8 turns dropped that answered a field which does not exist, 8 refusals re-pointed at a
live field, and `Warehouse` mapped to `industrial` — no listing carries Warehouse.

---

## r4 — 102 turns, the real questionnaire

Same serving setup as r2: llama.cpp b10290, 6 threads, `--parallel 1`, `--cache-reuse 256`,
i7-10750H. All rows `--split all --no-next-question`. Prompt is 2689 chars, down from 3983,
because the schema now describes four questions instead of six.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-lora-v2-q4km-r4 | LoRA v2 Q4_K_M | 102 | 0.990 | 0.805 | 0.921 | 0.859 | 0.657 | 0.690 | 0.707 | 1256 | 1689 |

```bash
python -m ml.eval.run --label 0.5b-lora-v2-q4km-r4 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v2-q4_k_m
```

**This is v2 measured outside the conditions it was tuned for.** The adapter was trained
against the six-question prompt with a three-key output object. It is not a ceiling for
what a model trained on r4 data would reach, and it should not be read as a regression
from r2's 0.926 — different questionnaire, different task.

### Removing `next_question` from the schema broke the adapter

The first r4 attempt scored raw JSON validity **0.794**: 21 of 102 replies were malformed,
all in the same shape.

```
{"extracted":{"price":{"max":2000000}},"skipped_fields":[}}
```

It stops exactly where the third key used to begin. v2's fine-tune encoded a three-key
object, so asking for two leaves it stranded mid-structure. Confirmed by running the same
four turns twice against the same model, changing only the schema: 4 broken with two keys,
4 valid with three.

`_extract_json_object` cannot salvage `[}}`, so those turns fail outright — in production,
not just in the harness. **A fine-tuned model's output shape is part of its contract; a
schema change is a breaking change to the weights, not a prompt edit.**

`next_question` is therefore back in the schema as a compatibility shim: required so the
learned shape stays valid, carrying no description so there is no prose to copy into a
reply, and its value discarded by `resolve_next_intake_question`. Raw JSON validity
returned to 0.990. Delete the shim once a model trained on the two-key schema is serving.

### Per category

| Category | Turns | Field F1 | Value acc | Skip recall |
|---|---|---|---|---|
| `skip` | 25 | 1.000 | 1.000 | 0.720 |
| `unit-ambiguity` | 12 | 1.000 | 0.750 | — |
| `bound-direction` | 8 | 0.941 | 0.500 | — |
| `multi-field` | 14 | 0.900 | 0.630 | — |
| `single-field` | 9 | 0.889 | 0.875 | — |
| `previously-skipped` | 8 | 0.800 | 0.500 | 0.875 |
| `correction` | 8 | 0.706 | 0.667 | — |
| `answer-and-skip` | 5 | 0.571 | 0.500 | 0.250 |
| `complete` | 5 | n/a | n/a | 0.750 |
| `empty-or-noise` | 8 | n/a | n/a | — |

`bound-direction` shows the split this project keeps rediscovering: field F1 0.941 with
value accuracy 0.500 means the right key and the right figure on the wrong side of the
range. The deterministic corrector in `app/domain/bounds.py` fixes that downstream, and
the harness cannot see it — it scores raw model output by design.

`answer-and-skip` remains the weakest shape at 5 turns, too few to resolve anything.

---

## Conventions the gold labels assume

- A bare budget figure is an upper bound: "half a million" → `price.max = 500000`.
- "at least N" sets `min`, "no more than N" / "under N" / "or less" sets `max`,
  "between A and B" sets both.
- An exact size with no qualifier sets `min` and `max` to the same value.
- `property_type` is a list even when one type is named.
- "buy" → `listing_type: "Sale"`, "lease"/"rent" → `"Lease"`.
- Answering a previously skipped field **clears** the skip.
- `next_question_key` is the first required key that is neither answered nor skipped, by
  `order_index`, and `null` once none remain.
- Location gold contains exactly what the message states — a message naming only a city is
  never labelled with a state.

**Next-question accuracy is not measured.** P1 removed `next_question.key` from the schema,
so no model emits one. Pass `--no-next-question`; scoring the question *text* would need a
different metric than exact match.

---

## r2 — 102 turns

llama.cpp b10290, 6 threads, `--parallel 1`, `--cache-reuse 256`, i7-10750H (6 physical
cores, AVX2, no AVX-512). All rows `--split all --no-next-question`.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-stock-q4km | stock Q4_K_M | 102 | 1.000 | 0.143 | 0.841 | 0.244 | 0.392 | 0.110 | 0.830 | 2955 | 4085 |
| 0.5b-lora-v1-q4km | LoRA v1 Q4_K_M | 102 | 0.990 | 0.899 | 0.909 | 0.904 | 0.825 | 0.848 | 0.596 | 1236 | 1716 |
| **0.5b-lora-v2-q4km** | **LoRA v2 Q4_K_M** | 102 | **1.000** | **0.931** | **0.920** | **0.926** | **0.840** | 0.844 | **0.809** | 1271 | 1727 |
| `7b-router` | the incumbent | — | **blocked on credits, see below** ||||||||

```bash
python -m ml.eval.run --label 0.5b-lora-v2-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v2-q4_k_m
```

### Skip recall cannot be read alone either

The stock model scores skip recall **0.830** — higher than tuned v1's 0.596. That is not
skill. Its skip *precision* is **0.110**: it dumps most required keys into `skipped_fields`
on every turn, so it "catches" refusals the way a stopped clock is right twice a day.

The pair is the story:

| | Skip precision | Skip recall |
|---|---|---|
| stock | 0.110 | 0.830 |
| v1 | 0.848 | 0.596 |
| **v2** | **0.844** | **0.809** |

v2 reaches essentially the stock model's recall while keeping v1's precision — nearly 8×
the precision at the same catch rate. This is the same lesson as field precision/recall:
one number of a pair is never a verdict.

### The v2 data pass worked, and why

v1 missed four of ten r1 refusals, and on r2's 25 it recalled **0.520** in the `skip`
category. The failure was legible: it returned empty `extracted` and then **re-asked the
very field being refused**, i.e. it classified refusals as noise. Both shapes produce empty
`extracted`, so wording is the only signal, and v1 trained on 14 fixed refusal strings —
it learned the strings, not the category. `"skip"` worked; `"pass"` did not, from the same
list.

v2 expanded the refusal vocabulary to ~60 phrasings across registers, over-weighted `skip`
(12.6% → 18.9% of the set), and added an `answer-and-skip` shape. Result:

| Category | v1 skip recall | v2 skip recall |
|---|---|---|
| `skip` | 0.520 | **0.840** |
| `previously-skipped` | 0.818 | **0.909** |
| `answer-and-skip` | 0.000 | 0.200 |

**The r2 eval turns deliberately use refusal phrasings absent from the training list**
("surprise me", "meh", "we're negotiable on that"), so this measures generalisation rather
than recall of a memorised set.

Field metrics improved alongside: F1 0.904 → 0.926, precision 0.899 → 0.931, raw JSON
validity 0.990 → 1.000, and `unit-ambiguity` F1 0.917 → 1.000. Latency is unchanged.

### Dev vs holdout: field metrics generalise, skip is underpowered

v2's data design was derived by inspecting **dev** failures, so scoring the splits apart
asks whether that design was fitted to the turns inspected.

| Split | Turns | Field F1 | Value acc | Skip prec | Skip recall |
|---|---|---|---|---|---|
| dev | 76 | 0.938 | 0.774 | 0.833 | 0.833 |
| holdout | 26 | 0.903 | **0.964** | 0.636 | 0.636 |

Field extraction generalises: F1 0.938 against 0.903, and value accuracy is *higher* on
holdout, which is the opposite of what fitting to dev would produce.

**Skip recall drops 0.833 to 0.636, and the honest reading is "cannot tell".** The holdout
contains 9 skip-bearing turns, about 11 gold skips. 7 of 11 has a 95% interval of roughly
0.35–0.87, which covers the dev rate — so this is not evidence of a real gap, and equally
not evidence against one. **The holdout is too small to resolve skip at all**, which is the
same measurement problem r2 was created to fix, one level down.

Do not act on the point estimate. Either grow the holdout's skip share before trusting a
split comparison for this metric, or judge skip on the full set and accept that no
held-out check of it exists yet.

### The remaining weakness is compound refusals

`answer-and-skip` — one message that answers one field and refuses another, e.g.
*"warehouse, and don't worry about the budget"* — sits at **0.200 skip recall**, 1 of 5.
v1 scored 0.000, so the new shape helped, but it is far from solved at 9.5% of the training
set. It is also only 5 eval turns, so the number is weak evidence either way; more turns
and a larger share of that shape are the next pass.

### The tuned model is 2.3× faster than stock

p50 2955 ms → 1271 ms, with no serving change. A model that emits only the fields present
writes far fewer tokens, and CPU generation is roughly linear in output length. Precision
and latency are one problem, not two.

---

## r1 — 52 turns (historical)

Superseded by r2. **Do not compare these rows to anything above.** They are retained
because two conclusions were measured internally consistently within this revision and
still hold.

| Label | Turns | Field F1 | Value acc | p50 ms |
|---|---|---|---|---|
| 0.5b-f16-local | 52 | 0.264 | 0.362 | 5102 |
| 0.5b-q4km-local | 52 | 0.259 | 0.421 | 2843 |
| 0.5b-lora-f16-local | 52 | 0.923 | 0.857 | 1692 |
| 0.5b-lora-q4km-local | 52 | 0.935 | 0.837 | 1262 |
| 0.5b-lora-q4km-imatrix | 52 | 0.901 | 0.805 | 1175 |

### INT4 costs nothing on this model

Stock F16 0.264 against Q4_K_M 0.259, and tuned F16 0.923 against Q4_K_M 0.935 — both
inside noise, in both directions. Meanwhile Q4 halves p50 for 398 MB of weights against
994 MB, which is the memory-bandwidth argument holding. **Keep Q4_K_M.** The pre-agreed
`Q5_K_M` fallback is unnecessary: there is no quantization regression to recover from.

### The importance matrix does not pay on this model

Calibrated on 400 training examples, ~50 min of `llama-imatrix`: F1 **0.901 against 0.935**
for the plain quant. Not an improvement.

`llama-quantize` reports the same `quant size = 373.71 MiB (6.35 BPW)` with and without it,
because bit allocation never changed — **144 of 290 tensors never reach `q4_K` at all**:

```
warning: blk.0.attn_output.weight - ncols 896 not divisible by 256
         (required for type q4_K) -> falling back to q5_0
```

Qwen2.5-0.5B's 896-wide tensors are not divisible by the 256-element `q4_K` superblock, so
half the model already sits at `q5_0`/`q6_K`. An imatrix steers value placement inside
`q4_K` blocks; where there are none, it has nothing to steer. `--token-embedding-type` and
`--output-tensor-type` at `q8_0` changed nothing for the same reason.

**Ship the plain `Q4_K_M`.** This conclusion is about this model's tensor geometry, not
about importance matrices in general.

### Grammar-constrained decoding would recover nothing

Raw JSON validity was already 1.000, with zero keys outside the question set. A grammar
enforces shape, and shape was never what was broken. Worth adding later as cheap insurance;
it is not a fix, and no phase should depend on it.

---

## The 7B row: attempted, still not measurable

The router accepted **6 calls** and then returned 402 again. The key, model id and harness
path are all fine — this is depleted credits, not configuration. The runner aborted on the
402 rather than burning the remaining turns, which is what `FATAL_STATUS` exists for.

The 5 scored turns were all `single-field`, the easiest category. **Not a baseline, not
comparable to anything.** Two hints worth confirming, not believing: the 7B also over-emits
(precision 0.500 on single-field gold), and the router showed p95 10985 ms against p50
1612 ms on five requests — a tail a warm local process does not have.

## What this does not settle

**The gate cannot close.** Everything above compares the 0.5B against itself. There is
still no measurement of the model this would replace, so "good enough" has no referent.
Restoring credits or setting `OPENROUTER_API_KEY` is the only thing in the way, and it
fixes the production outage at the same time.

## Later rows

| Label | What it establishes |
|---|---|
| `7b-router` | The incumbent, on r2. Everything else is measured against this |
| `0.5b-lora-v2-q4km-holdout` | Whether r2's holdout split agrees with the dev split |
| `0.5b-lora-v3-*` | Whether more `answer-and-skip` data fixes compound refusals |
