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
| 0.5b-f16-local | `qwen2.5-0.5b-instruct-f16` | local llama.cpp | 52 | 1.000 | 0.152 | 1.000 | 0.264 | 0.362 | 0.106 | 0.810 | 0.269 | 5102 | 6647 |
| 0.5b-q4km-local | `qwen2.5-0.5b-instruct-q4_k_m` | local llama.cpp | 52 | 1.000 | 0.154 | 0.809 | 0.259 | 0.421 | 0.094 | 0.762 | 0.269 | 2843 | 4713 |
| `7b-router` | — | HF router | — | **blocked on credits** |||||||||

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
