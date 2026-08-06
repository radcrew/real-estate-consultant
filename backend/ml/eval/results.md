# Intake extraction: eval results

Every row is one `ml/eval/run.py` invocation. **Record the command**, because a row is
only meaningful alongside the dataset revision, the split, and whether the duplicate
schema copy and JSON mode were on.

**Do not compare rows produced from different `questions.json` or `dataset.jsonl`
revisions.** If either changes, previous rows are historical and a new table starts.

## Conventions the gold labels assume

The dataset encodes these so scoring is deterministic. A model is not penalised for
disagreeing with them in prose, only for extracting different values.

- A bare budget figure is an upper bound: "half a million" → `price.max = 500000`.
- "at least N" sets `min`, "no more than N" / "under N" / "or less" sets `max`,
  "between A and B" sets both.
- An exact size with no qualifier sets `min` and `max` to the same value.
- `property_type` is a list even when one type is named.
- "buy" → `listing_type: "Sale"`, "lease"/"rent" → `"Lease"`.
- Answering a previously skipped field **clears** the skip rather than carrying it.
- `next_question_key` is the first required key that is neither answered nor skipped, by
  `order_index`, and `null` once none remain.

## Prompt size (P1)

Measured with `ml/eval/questions.json` (6 questions) on a turn with empty criteria.
Characters, not tokens — no tokenizer is installed, and P2's runs report exact
`prompt_tokens` from the endpoint.

| Prompt | Chars |
|---|---|
| Before: intake system + user | 4975 |
| Before: **what production sent**, incl. the provider's duplicate schema | **6022** |
| After P1 | **3983** |

A 33.9% reduction against what production actually sent. Three changes, roughly equal
thirds: dropping `missing_fields` and `is_complete` from the schema, reducing
`next_question` to `text` alone, and suppressing the provider's second schema copy.

Every baseline below is measured on the post-P1 prompt, since P1 landed before any row
was recorded. Use `--duplicate-schema` to reproduce the pre-P1 request.

## Baselines

Both local rows: full 52 turns (`--split all`), llama.cpp b10290, 6 threads, `--parallel 1`,
`--cache-reuse 256`, on an i7-10750H (6 physical cores, AVX2, no AVX-512).

| Label | Model | Endpoint | Turns | Raw JSON valid | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | Next-q acc | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-f16-local | `qwen2.5-0.5b-instruct-f16` | local llama.cpp | 52 | 1.000 | 0.152 | 1.000 | 0.264 | 0.362 | 0.106 | 0.810 | n/a | 5102 | 6647 |
| 0.5b-q4km-local | `qwen2.5-0.5b-instruct-q4_k_m` | local llama.cpp | 52 | 1.000 | 0.154 | 0.809 | 0.259 | 0.421 | 0.094 | 0.762 | n/a | 2843 | 4713 |
| **0.5b-lora-f16-local** | `qwen2.5-0.5b-instruct-intake-f16` | local llama.cpp | 52 | 1.000 | 0.955 | 0.894 | **0.923** | 0.857 | 0.882 | 0.714 | n/a | 1692 | 2598 |
| **0.5b-lora-q4km-local** | `qwen2.5-0.5b-instruct-intake-q4_k_m` | local llama.cpp | 52 | 1.000 | 0.956 | 0.915 | **0.935** | 0.837 | 0.889 | 0.762 | n/a | **1262** | **1801** |
| 0.5b-lora-q4km-imatrix | `…-q4_k_m-imatrix` | local llama.cpp | 52 | 1.000 | 0.932 | 0.872 | 0.901 | 0.805 | 0.889 | 0.762 | n/a | 1175 | 1555 |
| `7b-router` | — | HF router | — | **blocked on credits** |||||||||

**Next-question accuracy is not measured.** P1 removed `next_question.key` from the schema,
so no model emits one and the runner scored only the 14 null-gold turns as correct — 0.269
on every row, an artifact rather than a signal. Pass `--no-next-question` from here on;
scoring the question *text* would need a different metric than exact match.

```
python -m ml.quantize.build_gguf --model Qwen/Qwen2.5-0.5B-Instruct
python -m ml.serve.serve_local --model qwen2.5-0.5b-instruct-{f16,q4_k_m}.gguf
python -m ml.eval.run --label 0.5b-{f16,q4km}-local --split all \
  --base-url http://127.0.0.1:8080/v1 --api-key local --model qwen2.5-0.5b-instruct-{f16,q4_k_m}
```

Mean prompt tokens 929 on both rows, so the P1 slimming holds at the tokenizer level too.
Artifact sizes, which run above the plan's estimates: F16 994 MB, Q4_K_M 398 MB.
`llama-quantize` reported *144 of 290 tensors required fallback quantization* — the 0.5B's
896-wide tensors do not divide evenly for every K-quant, so much of the model lands at
q5_0/q6_K rather than q4_K. Q4_K_M on this model is closer to 6.35 bits per weight than to 4.

### What quantization costs: nothing measurable

Field F1 0.264 → 0.259 and skip recall 0.810 → 0.762 across 52 turns are well inside
noise; value accuracy actually rose, 0.362 → 0.421, which is the same story from the other
side. Raw JSON validity is 1.000 on both.

**p50 halves, 5102 ms → 2843 ms**, for 398 MB of weights against 994 MB. That is the
memory-bandwidth argument holding: generation reads the weights once per token, so
throughput tracks bytes read. INT4 is the right call and costs nothing here.

### The stock 0.5B is not usable for this task, at any precision

Precision 0.15 against recall near 1.0 means it emits roughly six times more fields than it
should. It is not extracting — it is echoing the schema. Every turn returns all six
properties, nulls included, and stuffs `skipped_fields` with most of the required keys:

```json
// input: "I'm looking in Austin, Texas"   (gold: one field)
{"extracted": {"location": "Austin, Texas", "property_type": ["Office","Retail"],
               "listing_type": "Sale", "price": null, "size_sqft": null, "loading_docks": null},
 "skipped_fields": ["location","property_type","listing_type","price","size_sqft"],
 "next_question": null}
```

`skipped_fields` contains `location` while `extracted` answers it — self-contradictory in a
single reply. On empty input it returns the *current criteria* as if freshly extracted, so
it cannot tell "the user said nothing" from "the user repeated themselves". The `skip`
category scores F1 0.036, the worst of the eight, which matters because skip handling is
what the prompt spends most of its words on.

### Grammar-constrained decoding would recover nothing here

Raw JSON validity is already **1.000** on both rows and no key fell outside the question set
(`invented_keys_total` 0). A grammar enforces shape, and the shape is not what is broken —
the model emits perfectly well-formed JSON that is semantically wrong. Worth adding as cheap
insurance later, but it is not the fix, and any plan that leans on it is leaning on nothing.

### Latency is driven by over-emission, not by the prompt

Mean completion is 107 tokens against a 929-token prompt. A model that emitted only the
fields actually present would produce perhaps 30 tokens, which on the same hardware lands
near 1 s. Precision and latency therefore share one root cause. Both are behavioural, which
is what a LoRA is for, so P5 should improve accuracy and speed together.

### The fine-tune fixes the over-emission, and the speed comes with it

600 examples, 1 epoch, ~2.8 h on 6 CPU cores. Against the stock Q4 row:

| | stock Q4 | LoRA Q4 |
|---|---|---|
| Field precision | 0.154 | **0.956** |
| Field F1 | 0.259 | **0.935** |
| Value accuracy | 0.421 | **0.837** |
| Skip precision | 0.094 | **0.889** |
| p50 | 2843 ms | **1262 ms** |

Precision moved 0.15 → 0.96 while recall held, which is the whole thesis: the stock model
found every field and could not stop, and the training set was built almost entirely to
teach restraint. The **latency followed for free** — 2.3× faster than stock Q4 and 4× faster
than stock F16, because a model that emits only the fields present writes far fewer tokens.
Nothing about the serving configuration changed between those rows.

Per category, the LoRA Q4 scores 1.000 on `single-field`, `correction`, `complete` and
`previously-skipped`, and 0.895 on `multi-field`.

**The weak spot is skip detection**: category F1 0.667, skip recall 0.600. The model
usually gets the skip right when it acts, but misses four of ten refusals outright. That is
the obvious target for the next data pass — `skip` was 13% of the training set after
deduplication, against a design intent of 20%, because refusal phrasings come from a fixed
list and collapse under dedup.

### Quantization is still free after fine-tuning

F1 0.923 at F16 against 0.935 at Q4_K_M — the quantized model scores marginally *higher*,
which on 52 turns means the gap is noise. The pre-agreed fallback to `Q5_K_M` is not needed:
there is no regression to recover. Q4_K_M is also 1.3× faster and 398 MB against 994 MB.

### The importance matrix does not pay on this model

Calibrated on 400 training examples (1.7 MB), ~50 min of `llama-imatrix` on 6 cores.
Result: F1 **0.901 against 0.935** for the plain quant, value accuracy 0.805 against 0.837.
Not an improvement, and if anything slightly worse.

The reason is visible in the quantizer output. `llama-quantize` reports the same
`quant size = 373.71 MiB (6.35 BPW)` with and without the imatrix, because bit allocation
did not change — and it did not change because **144 of 290 tensors never reach `q4_K` at
all**:

```
warning: blk.0.attn_output.weight - ncols 896 not divisible by 256
         (required for type q4_K) -> falling back to q5_0
```

The 0.5B's 896-wide tensors are not divisible by the 256-element `q4_K` superblock, so half
the model already sits at `q5_0`/`q6_K`. An imatrix steers value placement inside `q4_K`
blocks; where there are no `q4_K` blocks, it has nothing to steer. `--token-embedding-type`
and `--output-tensor-type` at `q8_0` likewise changed nothing, because the fallback had
already promoted those tensors.

**Ship the plain `Q4_K_M`.** The imatrix step costs an hour per build and buys nothing here.
It is worth revisiting only on a model whose tensor shapes divide evenly — this conclusion
is about Qwen2.5-0.5B's geometry, not about importance matrices in general.

The pre-agreed `Q5_K_M` fallback is also unnecessary: there was no quantization regression
to recover from in the first place.

### What this does not settle

The `7b-router` row is still missing, so **the gate cannot close**. Everything above compares
the student against itself; none of it says whether the incumbent is too slow to keep. That
row needs credits or an OpenRouter key and nothing else.

Later phases add rows rather than editing existing ones:

| Label | What it establishes |
|---|---|
| `0.5b-q4km-grammar` | What constrained decoding recovers |
| `0.5b-lora-bf16` | Whether fine-tuning beat the stock model |
| `0.5b-lora-q4km-imatrix` | The artifact that would actually ship |

Write the regression threshold for the last row **before** running it, not after.
