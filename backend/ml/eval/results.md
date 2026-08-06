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

No rows yet. P2 fills these in.

| Label | Model | Endpoint | Turns | Raw JSON valid | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | Next-q acc | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

Rows to produce, in this order:

| Label | What it establishes | Blocked by |
|---|---|---|
| `7b-router` | The incumbent. Everything else is measured against this | HF credits |
| `0.5b-f16-local` | The stock student before quantization | nothing |
| `0.5b-q4km-local` | What INT4 alone costs, before any training | nothing |

Later phases add rows rather than editing existing ones:

| Label | What it establishes |
|---|---|
| `0.5b-q4km-grammar` | What constrained decoding recovers |
| `0.5b-lora-bf16` | Whether fine-tuning beat the stock model |
| `0.5b-lora-q4km-imatrix` | The artifact that would actually ship |

Write the regression threshold for the last row **before** running it, not after.
