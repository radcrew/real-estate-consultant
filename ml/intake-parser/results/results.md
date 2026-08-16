# Intake extraction: eval results

Every row is one `pipeline/eval/run.py` invocation. **Record the command**, because a row is
only meaningful alongside the dataset revision, the split, and whether the duplicate
schema copy and JSON mode were on.

**Rows from different `eval.jsonl` revisions are not comparable and must not share a
table.** When the dataset changes, previous rows become historical and a new table starts.

## Dataset revisions

| Rev | Turns | Questionnaire | Notes |
|---|---|---|---|
| **r8 (current)** | 129 | the real one | Same turns as r7. Eight size golds moved from exact to max-only, following the convention change: a bare figure carrying a unit is a ceiling. First scored by v6 |
| r7 | 129 | the real one | Square yards, `ground` as a type, and budgets past $5M — 11 turns from two reported messages. First scored by v5 |
| r6 | 118 | the real one | `pending-answer` added — 7 turns on bare values, plus 3 unmarked corrections |
| r5 | 108 | the real one | `property-synonym` added — 6 turns on wordings the generator never emits |
| r4 | 102 | the real one | First revision built from the live `questions` table |
| r3 | 110 | fictional | `bound-direction` added, skip turns decontaminated. Never published |
| r2 | 102 | fictional | skip 10 → 25, new `answer-and-skip` category |
| r1 | 52 | fictional | Original set |

r1's 10 skip turns meant skip recall could not resolve anything finer than 0.1, which was
useless for judging a change aimed squarely at skip detection. That is why r2 exists.

### Everything before r4 was scored against a questionnaire that does not exist

`datasets/questions.json` was hand-written when the harness was built and never checked
against the database. It described **six** questions; the `questions` table has held
**four** since 2026-04-21, and nothing on this branch added or removed a row. So
`listing_type` and `loading_docks` have never existed, `where_criteria` does not filter on
them, and **92 of r3's 110 turns referenced one of them**. A further 50 used property
types the questionnaire never offered.

Every r1, r2 and r3 number was therefore measured on a longer prompt with two extra
extraction targets than production has ever sent. Those rows are kept below because the
comparisons *within* a revision were internally consistent — INT4 costing nothing, v1
against v2 — but no absolute figure from them describes the shipped product.

r4 is a dump of the live table (`pipeline.data.dump_questions`), with the dataset rebuilt against
it: 8 turns dropped that answered a field which does not exist, 8 refusals re-pointed at a
live field, and `Warehouse` mapped to `industrial` — no listing carries Warehouse.

---

## r8 — 129 turns, bare sizes golded as ceilings

Same 129 turns as r7 and the same binaries and serving flags — `.local/bin` unchanged, 6
threads, `--parallel 1`, `--cache-reuse 256`, `-c 4096`, i7-10750H. All rows `--split all
--no-next-question`.

**No turn was added or reworded. Eight golds changed shape.** A bare figure carrying a
unit is now a ceiling rather than an exact area, so `10,000 square feet`, `20,000 sqft`
(×2), `5,000 sqft`, `8,000 sqft`, `1,500 yards`, `800 gaj` and `1500 yard` moved from
`{"min": n, "max": n}` to `{"max": n}`. The two unitless answers — `5,000` and `25k`
against the size question — stay exact, which is the v3 lesson: max-only there turned an
answer of `32` into a 32 sqft ceiling that every later correction stacked against.

Rows are therefore not comparable with r7, and v5 was re-scored here to give v6 something
to be measured against.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-lora-v6-f16 | LoRA v6 F16 | 129 | 1.000 | **0.971** | 0.962 | **0.967** | **0.931** | **0.897** | 0.854 | 1187 | 2021 |
| **0.5b-lora-v6-q4km** | **LoRA v6 Q4_K_M** | 129 | 1.000 | 0.944 | 0.962 | 0.953 | **0.912** | 0.881 | **0.902** | 1020 | 1366 |
| 0.5b-lora-v5-q4km-r8 | LoRA v5 Q4_K_M | 129 | 1.000 | 0.944 | 0.962 | 0.953 | 0.853 | 0.854 | 0.854 | 1027 | 1490 |

```bash
python -m pipeline.serve.serve_local --model qwen2.5-0.5b-instruct-intake-v6-q4_k_m.gguf
python -m pipeline.eval.run --label 0.5b-lora-v6-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v6-q4_k_m
```

Artifact sizes are unchanged from v5: 994 MB F16, 398 MB Q4_K_M, 6.35 BPW, 144 of 290
tensors requiring fallback quantization. Only `train.jsonl` changed between v5 and v6 —
same base, same adapter hyperparameters (r=16, alpha=32, dropout 0.05, all seven
projections), 338 steps × batch 2 × grad-accum 4 against 2,700 rows, one epoch. Final
eval loss rose, 0.0110 to 0.0278, which is the harder set rather than a worse fit.

### What the data change bought, and what it cost

Field F1 is flat at 0.953. **Value accuracy carries the whole result: 0.853 to 0.912.**
Per-turn, v6 fixes 10 and regresses 4, net +6, 100 → 106 of 129 passing.

Five of the ten fixes are the re-golded turns themselves, which only says v6 learned the
convention it was trained on. The other five are not: `multi-four-fields`,
`complete-after-skips`, `single-type-land`, `complete-add-docks-after-skips` and
`bound-max-shy-of`. `unit-ambiguity` moved 0.810 → 0.905 on 20 turns.

The four regressions, each read from `raw_output`:

| Turn | Input | v6 | v5 |
|---|---|---|---|
| `type-ground-alone` | `just open ground for now` | `{}` | `property_type: ["land"]` |
| `gibberish` | `asdkjfh`, prior Austin | echoed `location: Austin, Texas` | `{}` |
| `skip-surprise-me` | `surprise me` | no skip | `skipped: property_type` |
| `bound-split-two-clauses` | `lower than $2M, higher than $500K` | `200000-500000` | correct |

**`type-ground-alone` is a cost of the fix, not noise.** r7 records `ground` as
knife-edge — 8 land-sense messages against 18 for `ground floor`, so the token's own
statistics said *ignore me*, which is why ambiguous phrasings are weighted 8×. v6 adds 74
messages that are nothing but an unmapped clause, gold empty, and `ground floor only` and
`top floor` are among them. That is the same balance tipping back. If the 8× weight is
raised to compensate, this is the turn to watch.

### The two production failures this revision was built for, neither of which it scores

Both were reported from the app and both are fixed, but the eval cannot see either — no
turn golds a size at or above 100,000 sqft, and no turn is a standalone unmapped clause.
Measured by probing the served model through `build_intake_messages`:

| Message | v5 behaviour | v6 |
|---|---|---|
| `I need a 100k sqft industrial warehouse with 32ft clear height in Chicago` | `price: 100000`, no size | `size_sqft {"max": 100000}`, `industrial`, `Chicago` |
| `3 floors`, with `property_type: ["office"]` already set | overwrote type with `multifamily` | `{}`, office untouched |

The first is the sentence `INTAKE_OPENING_MESSAGE` suggests to every user. It failed
because `_sqft_value` stopped at 59,500 while `_price_value` draws exactly 100,000 in ~2%
of budgets, so `100k` had only ever been money. **Turns for both belong in r9**; until
they exist, these two rows are the only evidence and they are not in the table.

### Where the units still fail, and why it is the same defect again

Probing past the sampler ranges finds the bug class that produced this revision, twice
more:

| Message | v6 | Correct | Sampler range |
|---|---|---|---|
| `130k yard` | 117,000 | 1,170,000 | yards stop at 6,500 |
| `130k square meters` | 165,000 | 1,399,307 | metres stop at 90,000 m² |
| `$10M` | 1,000,000 | 10,000,000 | *inside* the 5M–60M band |

The first two are coverage: a figure past where the sampler stops is a shape the model was
taught is impossible rather than rare, which is exactly what `_price_value` documents and
what `_sqft_value` was just fixed for. The third is not — $10M is well inside the band, so
that one is model error at 0.5B, and it is worth noting the backend discards it anyway
since `correct_bound_direction` drops a bound whose value appears nowhere in the message.

Square metres are the weakest addition. ×10.7639 is a genuinely harder conversion than the
yards' ×9, and 1,399,307 does not fall out of pattern-matching. It deserves its own eval
category rather than being smeared across `unit-ambiguity`.

---

## r7 — 129 turns, square yards, the `ground` collision, and budgets past $5M

Same binaries and serving flags as r6 — `.local/bin` unchanged, 6 threads, `--parallel 1`,
`--cache-reuse 256`, `-c 4096`, i7-10750H. All rows `--split all --no-next-question`.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-lora-v5-f16 | LoRA v5 F16 | 129 | 1.000 | **0.963** | **0.972** | **0.967** | **0.951** | 0.850 | 0.829 | 1274 | 3370 |
| **0.5b-lora-v5-q4km** | **LoRA v5 Q4_K_M** | 129 | 1.000 | 0.944 | 0.962 | **0.953** | **0.931** | 0.854 | 0.854 | 1106 | 1624 |
| 0.5b-lora-v4-q4km-r7 | LoRA v4 Q4_K_M | 129 | 1.000 | 0.907 | 0.915 | 0.911 | 0.804 | 0.886 | 0.756 | 1082 | 1631 |

```bash
python -m pipeline.eval.run --label 0.5b-lora-v4-q4km-r7 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m

python -m pipeline.eval.run --label 0.5b-lora-v5-f16 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v5-f16

python -m pipeline.eval.run --label 0.5b-lora-v5-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v5-q4_k_m
```

The v4 row is a re-score, not a new model — the r6 table measures the same GGUF on 118
turns. It is here so v5 has a baseline on the instrument it is judged by, and it is the
only v4 number comparable to a v5 number.

**v5 is v4's recipe with different data.** Same base, same LoRA config, same
`num_train_epochs=1` / 338 steps, seed 17. Only `train.jsonl` changed — it now carries
`pending_question`, the `correction` and `pending-answer` shapes, square yards, 8×
ambiguous phrasings, two- and three-digit M-notation, and symmetric bound vocabulary. So
every difference below is attributable to the training set.

Eleven turns from two reported messages. Every one of the four defects below is a gap in
what the generator could produce, and none of them was reachable by the eval as it stood.

### `from $30M to $40M` → `3,000,000 - 4,000,000`

A factor of ten, in both bounds. Not a parse failure: `_price_value` stopped at $4.9M, so
**every M-notation figure the set had ever produced carried a single digit before the
decimal point** — integer parts 0 through 8, never two. `$30M` was a token shape the model
had never seen, and `$3.0M`, which it had seen hundreds of times, is one dot away.

| | before | after |
|---|---|---|
| price golds `< $1M` | 596 | 514 |
| `$1–5M` | 257 | 208 |
| `$5–10M` | 17 | 25 |
| `$10–100M` | **0** | 117 |
| `≥ $100M` | **0** | 29 |
| M-notation, two-digit integer part | **0** | 117 |
| M-notation, three-digit | **0** | 27 |

Widening the sampler forced a second change. `high = low + sample()` draws the two ends of
a range from unrelated bands, which was merely odd at `between $25,000 and $4.5M` and is
untenable at $150M, where the same line pairs a $45,000 floor with a $92.5M ceiling. The
span is now proportional to the floor, so both ends stay in one world at any magnitude,
and the ceiling is rounded on its **own** magnitude rather than the floor's — a $950,000
floor rounded on the floor's grain gives $1,905,000, which `_fmt_money` writes as `$1905k`.

### `warehouse, restaurant, shop, 1500 yard ground`

Returned `property_type: [industrial, retail, retail]` and no size. Three defects, and only
one of them was the model:

**The repeat was ours.** `drop_unconfigured_choices` canonicalises `shop` and `restaurant`
onto the same stored value and never deduplicated, so the duplicate was created by that
function rather than passed through it. The model was right to emit all three — it read
three things the client named. Worth noting that no eval row in this file would ever have
caught it: `pipeline/eval/metrics.py` normalises a list to a `frozenset`, so a repeated value
scores identical to a clean one. It is a defect in what the client is shown, not in
extraction, and it is fixed in the domain layer with `tests/domain/test_intake_choices.py`.

**`ground` lost to `ground floor`.** `ground` is a configured `land` phrasing, and
`ground floor` is a `DISTRACTORS` entry the set teaches the model to ignore. Counted on
the training set behind these models, the ignore sense outnumbered the type sense 18 to 8
— so the token's own statistics said "skip me". Same shape as `SF`/San Francisco and the
`floor` fix above; only the ratio was wrong.

Ambiguous phrasings are now drawn 8×, and `ground floor` stays exactly where it was. The
weight is measured rather than picked: at 4× the two senses landed within noise of each
other — five seeds ran 16v19, 18v16, 25v7, 11v14, 17v16, so which sense won came down to
the draw. At 8× the worst of those five is 1.3:1 while `ground` still takes only about a
quarter of `land`'s mentions. `TestAmbiguousTypeWords` aggregates over three seeds for the
same reason: a property that holds only on a lucky seed is not the property this needs.

**`1500 yard` could not have been extracted.** All 22 occurrences of `yard` in the set were
`fenced yard`, a distractor: the only thing the word had ever been used for was noise.
There was no square-yard unit anywhere and nothing converted. Square yards are now a
size unit with the gold in sqft — `1,500 yards` golds 13,500 — which makes it **the only
unit in the set where the stated figure and the gold figure differ**, so it is the only
place the model has to convert rather than copy.

Yards are deliberately kept out of two-figure phrasings. Each side of a range renders
independently, so no shared unit can be agreed: a hyphenated range whose high side picks
yards produces `9,000-1,500 yards`, and no reading of that text yields the gold. A plot is
quoted as a single figure anyway. `TestSquareYards` pins the conversion, the single-figure
rule and the surviving `fenced yard` distractor.

### The turns

8 dev / 3 holdout. Both reported messages are in the set intact — `type-ground-trailing`
and `unit-price-two-digit-millions` — and each is paired with turns that isolate one
variable, so a failure on a compound turn can be attributed rather than guessed at:

* `type-ground-alone` and `type-ground-floor-is-not-land` split the two senses of `ground`.
* `unit-price-single-digit-millions` is `from $3M to $4M`, the same sentence one order of
  magnitude down. A model that reads the leading digit and drops the rest scores exactly
  one of the pair — the same design as r6's matched `5,000`.
* `unit-fenced-yard-is-not-a-size` keeps the distractor honest: `yard` with no figure in
  front of it still states no size.

### v5 clears 22 of v4's 41 failures and regresses 4

Counted as whole turns — every field, every value and every skip correct:

| | Turns fully correct |
|---|---|
| v4 Q4_K_M | 88 / 129 |
| v5 F16 | **108 / 129** |
| v5 Q4_K_M | **106 / 129** |

Per category, v4 Q4 → v5 Q4 (field F1 / value acc / skip recall):

| Category | Turns | Field F1 | Value acc | Skip recall |
|---|---|---|---|---|
| `unit-ambiguity` | 20 | 0.905 → **1.000** | 0.632 → **0.952** | — |
| `bound-direction` | 8 | 1.000 → 1.000 | 0.375 → **0.875** | — |
| `pending-answer` | 7 | 0.714 → **0.857** | 0.800 → **1.000** | — |
| `correction` | 11 | 0.909 → 0.909 | 0.800 → **0.900** | — |
| `single-field` | 10 | 0.947 → **1.000** | 0.889 → 0.900 | — |
| `multi-field` | 16 | 0.955 → **0.985** | 0.906 → 0.909 | — |
| `skip` | 25 | 1.000 → 1.000 | 1.000 → 1.000 | 0.840 → **0.920** |
| `previously-skipped` | 8 | 0.889 → 0.889 | 1.000 → 1.000 | 0.750 → 0.875 |
| `property-synonym` | 6 | 0.833 → 0.833 | 1.000 → 1.000 | — |
| `answer-and-skip` | 5 | 0.889 → 0.889 | 1.000 → 1.000 | 1.000 → 0.750 |
| `complete` | 5 | n/a | n/a | 0.000 → 0.500 |
| `empty-or-noise` | 8 | n/a | n/a | — |

`unit-ambiguity` and `bound-direction` are where the data work landed, and both were aimed
at directly. Nothing regressed at category level except `answer-and-skip` and `complete`,
both at 5 turns, where one turn is 0.200 and neither movement is readable.

### The r7 additions: 8 of 9, and the one that fails is the compound

| Turn | v4 Q4 | v5 Q4 | Split |
|---|---|---|---|
| `type-ground-alone` | fail | **pass** | dev |
| `type-ground-floor-is-not-land` | pass | pass | dev |
| `unit-yards-bare` | fail | **pass** | dev |
| `unit-yards-gaj` | fail | **pass** | holdout |
| `unit-yards-min-bound` | fail | **pass** | dev |
| `unit-fenced-yard-is-not-a-size` | pass | pass | dev |
| `unit-price-two-digit-millions` | fail | **pass** | dev |
| `unit-price-single-digit-millions` | pass | pass | dev |
| `type-ground-trailing` | fail | **fail** | holdout |

The isolating turns are what make the remaining failure legible. `ground` in both senses,
yards in all three phrasings, and both magnitudes of M-notation now pass **individually** —
so neither the 8× weighting nor the square-yard unit nor the widened price sampler is
still missing. What fails is only the compound, `warehouse, restaurant, shop, 1500 yard
ground`:

```
gold  property_type [industrial, retail, land]   size_sqft {min: 13500, max: 13500}
v5    property_type [industrial, retail, retail] size_sqft {min: 13500, max: 13500}
```

**The yard conversion landed** — 1,500 → 13,500, the one place in the set where gold and
stated figure differ. `ground` is dropped only when it trails three other type words, which
is a compound-parse limit rather than the vocabulary gap the 8× weight was measured
against. Worth noting the duplicate `retail` is now emitted by the *model*, where the
reported production repeat came from `drop_unconfigured_choices`; `metrics.py` normalises
the list to a `frozenset`, so it costs nothing here and the domain-layer dedupe removes it
downstream. The missing `land` is the whole failure.

### `bound-direction` finally moves

0.375 across v3 Q4, v4 F16 and v4 Q4 — identical to three decimals — and **0.875** on both
v5 artifacts. Four of the five recorded failures pass:

| Turn | v4 Q4 | v5 Q4 |
|---|---|---|
| `bound-min-floor` | `price {max}` | **`price {min}`** |
| `bound-min-nothing-below` | `size_sqft {max}` | **`size_sqft {min}`** |
| `bound-split-two-clauses` | inverted range | **`{min: 500000, max: 2000000}`** |
| `bound-split-floor-ceiling` | `{min: 500000, max: 500000}` | **`{min: 500000, max: 2000000}`** |
| `bound-max-shy-of` | `size_sqft {min}` | `size_sqft {min}` |

`just shy of` is the one still wrong, and it is the one the training set is *not allowed* to
contain: `TestBoundWordingEvalSeparation` rejects any template reproducing an eval wording,
and this turn's phrasing is one of the two that were caught doing exactly that. It is
therefore the only honest generalisation reading in the category, and it is still 0/1.

### What quantization costs, and three of the four regressions are it

F16 → Q4_K_M: field F1 0.967 → 0.953, value accuracy 0.951 → 0.931, two turns. That is
about half what it cost v4 on r6 (0.951 → 0.925), and p95 falls 3370 → 1624 ms.

Four turns pass on v4 and fail on v5 Q4. **F16 gets three of them right**, so they are
quantization damage rather than a training regression:

| Turn | v5 Q4 emitted | Gold | F16 |
|---|---|---|---|
| `multi-four-fields` | `price {min: 3000000}` | `price {max}` | pass |
| `single-type-land` | spurious `skipped_fields: [location]` | `[]` | pass |
| `multi-two-types-and-city` | `[industrial, warehouse]` | `[industrial]` | pass |
| `carry-two-then-unskip` | `property_type` in both `extracted` and `skipped_fields` | skip `price` only | fail |

`multi-four-fields` is the sharpest of these — `under $3M` read as a floor, on a holdout
turn, in the category the bound work just fixed. `multi-two-types-and-city` is cosmetic in
production: `warehouse` is unconfigured, so the domain layer canonicalises and dedupes it
back to `[industrial]`.

Only `carry-two-then-unskip` fails at both precisions, and it violates an invariant the
generator enforces on every training row — **no key appears in both `extracted` and
`skipped_fields`**. Two other turns show the same shape (`carry-skip-unskip`,
`as-type-and-listing`), so it is a pattern rather than one draw.

### Still open

* **`pending-bare-size-k`** — `25k` against a pending size question still lands as
  `price {max: 25000}`. Unchanged from v3 and v4; the only r6 attribution failure the new
  `pending-answer` data did not fix, and the category otherwise scores value accuracy 1.000.
* **Spurious skips are the remaining precision cost.** Skip precision 0.854 against v4's
  0.886 is the one headline number that did not improve, and the invented-skip turns above
  are why.
* **The scorer cannot see a hallucinated skip of a non-field.** `correct-type-narrow` emits
  `skipped_fields: ["flex"]` and scores `skip_fp = 0`, because `flex` is not a question key
  and is dropped before comparison; `invented_keys_total` counts only `extracted`, so it
  reads 0. `single-type-land`'s `["location"]` scores 1 for the same behaviour. Worth
  closing before skip precision is used as a gate.
* **`complete` skip recall is honest for the first time.** v5 is the first model trained
  after the `_rough_up` hold-out leak was fixed, so 0.500 here is not comparable to the
  optimistic numbers in every row above it. On 5 turns it resolves nothing either way.
* **The gate still cannot close.** Nothing here measures the 7B incumbent; see below.

### Artifact sizes

| File | On disk | Note |
|---|---|---|
| `qwen2.5-0.5b-instruct-intake-v5-f16.gguf` | 994 MB | conversion target, eval baseline |
| `qwen2.5-0.5b-instruct-intake-v5-q4_k_m.gguf` | 398 MB | `quant size = 373.71 MiB (6.35 BPW)` |

144 of 290 tensors required fallback quantization, identical to v2, v3 and v4 — the 896-wide
tensors still do not divide evenly for every K-quant. No imatrix: measured at 0.901 against
0.935 on r1 and not retried.

---

## r6 — 118 turns, `pending-answer` added

Same serving setup as r5: llama.cpp b10290, 6 threads, `--parallel 1`, `--cache-reuse 256`,
i7-10750H. All rows `--split all --no-next-question`.

r5 could not measure the change it was about to be used to judge. Nothing in it asked the
model to attribute a value that the message alone does not identify — the only short inputs
were `''`, `meh`, `yep`, `...`, `ok`, all noise or refusals — so a fix for *"10" answering
the size question became a $10 budget* would have scored identically to no fix at all.

r6 adds seven `pending-answer` turns and three unmarked corrections. The sharpest is a
matched pair: `5,000` under two different `current_criteria`, gold `price` in one and
`size_sqft` in the other. Identical message, different answer, and nothing but
`pending_question` separates them — a model reading magnitude instead of the pending
question gets exactly one of the two wrong.

The three unmarked corrections exist because all eight r5 corrections carry a marker
(`actually`, `scratch that`, `change that to`). The bare form — `5,000 sqft` after a wrong
size — is the one that failed in production, and it was untested.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-lora-v4-f16 | LoRA v4 F16 | 118 | 1.000 | **0.946** | **0.957** | **0.951** | **0.864** | 0.838 | 0.756 | 1185 | 2398 |
| **0.5b-lora-v4-q4km** | **LoRA v4 Q4_K_M** | 118 | 1.000 | 0.915 | 0.935 | **0.925** | **0.849** | 0.912 | 0.756 | 865 | 1306 |
| 0.5b-lora-v3-q4km-r6 | LoRA v3 Q4_K_M | 118 | 1.000 | 0.832 | 0.913 | 0.870 | 0.821 | 0.914 | 0.780 | 1079 | 1599 |

```bash
python -m pipeline.eval.run --label 0.5b-lora-v3-q4km-r6 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v3-q4_k_m

python -m pipeline.eval.run --label 0.5b-lora-v4-f16 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v4-f16

python -m pipeline.eval.run --label 0.5b-lora-v4-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v4-q4_k_m
```

The v3 row is a re-score, not a new model — the r5 row below measures the same GGUF on 108
turns. It is here so v4 has a baseline on the instrument it is judged by.

### What this v4 is, and is not

**This v4 was trained on the dataset generated *before* `pending_question` existed.** The
`train.jsonl` behind it carries the seven old shapes and no `pending_question` key —
verified, not assumed. Its gains over v3 come from the earlier generator work (wider
vocabulary, multi-field sentences, exact bare sizes); the `correction` and `pending-answer`
shapes are **not** in it, and neither is the prompt field they teach.

That makes the row a useful control rather than a result: it is what the new eval turns
score when the fix is absent, on a model that is otherwise ahead of v3.

Quantization costs what it usually costs here — F1 0.951 → 0.925, value accuracy
0.864 → 0.849 — and buys back a third of the latency (p50 1185 → 865 ms).

### Where it still fails, and why that is the point

Q4 misses 4 of the 10 r6 additions, in three distinct modes:

| Turn | Emitted | Gold | Mode |
|---|---|---|---|
| `pending-bare-size-k` | `price {max: 250000}` | `size_sqft {min/max: 25000}` | Attribution — `25k` went to the wrong field, and misparsed |
| `pending-bare-5000-as-size` | `price {max: 5000000}` | `size_sqft {min/max: 5000}` | Echo — repeated the stored budget verbatim |
| `correct-size-bare` | `size_sqft {min: 5000, max: 10000}` | `size_sqft {min/max: 5000}` | Correction stacked against the old bound |
| `pending-bare-5000-as-price` | `price {value: 5000}` | `price {max: 5000}` | Invented key; F16 gets this one right, so it is quantization damage |

The first three are precisely what `pending-answer` and `correction` exist to teach, and
this model saw neither. The echo case is the clearest: `current_criteria` held
`price {max: 5000000}` and the reply `5,000` came back as that same stored ceiling.

`pending-overridden-by-unit` **passes** at both F16 and Q4 where v3 failed it — the bare
size read as exact rather than as a ceiling. That fix was in the earlier generator commit
and is already in this training set, which is why it moved and the other three did not.

So the numbers to beat with a v4 trained on the current data are
**`pending-answer` value accuracy 0.800 and `correction` 0.800**, not v3's 0.667/0.800.
A retrained v4 needs a distinct label; this row already owns `0.5b-lora-v4-q4km`.

### The v3 baseline, for contrast

v3 fails 4 of the 10 new turns, and the split matters:

| Turn | v3 emitted | Gold | What it shows |
|---|---|---|---|
| `pending-bare-size-k` | `price {max: 25000}` | `size_sqft {min/max: 25000}` | Attribution. `25k` went to the wrong field entirely |
| `pending-bare-5000-as-size` | `size_sqft {max: 5000}` | `size_sqft {min/max: 5000}` | Right field, ceiling instead of exact |
| `pending-overridden-by-unit` | `size_sqft {max: 20000}` | `size_sqft {min/max: 20000}` | Right field, ceiling instead of exact |
| `correct-size-bare` | `size_sqft {max: 5000}` | `size_sqft {min/max: 5000}` | Correction landed, ceiling instead of exact |

Only the first is a pure attribution miss. The other three are the max-only bare bound
`pipeline/data/generate.py` documents — a bare size read as a ceiling of 5,000 sqft rather than a
size of 5,000 — which is a search that matches nothing in production. The v4 row above
clears exactly one of them (`pending-overridden-by-unit`), which is the part its training
set actually covered.

Both models get the matched pair half-right, and both miss the same half: `5,000` scores as
a price and fails as a size. That is what reading magnitude instead of `pending_question`
looks like, and it is unchanged from v3 to this v4 — as it must be, since neither was
trained on the field.

### `bound-direction` is the weakest cell in the table, and it is a vocabulary gap

Value accuracy **0.375 on all three rows** — v3 Q4, v4 F16, v4 Q4 — identical to three
decimals across two training runs and two quantizations. That rules out noise and rules
out the quantizer. v4 scores field F1 **1.000** on the same eight turns: right field,
right figure, wrong direction.

| Turn | Message | Gold | v4 Q4 emitted |
|---|---|---|---|
| `bound-min-floor` | `$400k floor on the budget` | `price {min}` | `price {max: 400000}` |
| `bound-min-nothing-below` | `nothing below 5,000 sqft` | `size_sqft {min}` | `size_sqft {max: 5000}` |
| `bound-max-shy-of` | `just shy of 8,000 square feet` | `size_sqft {max}` | `size_sqft {min: 8000}` |
| `bound-split-two-clauses` | `… lower than $2M, … higher than $500K` | `{min: 500000, max: 2000000}` | `{min: 2000000, max: 500000}` |
| `bound-split-floor-ceiling` | `$500K floor, $2M ceiling` | `{min: 500000, max: 2000000}` | `{min: 500000, max: 500000}` |

Counted on the training set behind these models, the cause is not subtle: `ceiling` 0,
`shy of` 0, `nothing below` 0, `no lower` 0, `at minimum` 0 — and every occurrence of
`floor` was `ground floor` / `top floor` / `office floor`, a storey rather than a budget
floor. Three of the five failures are words the set never used in their bound sense.

The other two are structural, and the pairs that pass make the diagnosis exact:

* `nothing over $2M` **passes** and `nothing below 5,000 sqft` **fails**. The max list
  carried a negated form (`not over`) and the min list carried none, so the model learned
  to negate in one direction only.
* Both split turns state the ceiling first and both come back positionally — first figure
  to `min`, second to `max`, comparators ignored. Every `between` template put the low
  figure first, so position and direction never once disagreed in training. F16 emits
  `{min: 2000000, max: 500000}`: an inverted range, which no gold label has ever contained.

`pipeline/data/generate.py` now carries symmetric negations (five per direction), `floor` and
`ceiling` in their bound sense alongside the storey sense already in `DISTRACTORS`, and a
`REVERSED_BETWEEN_PHRASES` list at ~23% of two-sided ranges. Pinned by
`TestBoundDirectionVocabulary`. None of it is an eval wording — `nothing over {v}` and
`just shy of {v}` were both in the first draft, both are a turn above verbatim, and
`TestBoundWordingEvalSeparation` now rejects any template that reproduces one.

**Unrelated leak found while checking that.** The eval hold-out compared raw strings, but
`_rough_up` runs *after* an example is built, so seven rows carrying two eval wordings
shipped into this training set: `that's everything` four ways (upper-cased,
sentence-cased, with a full stop, with `!!`) and `yes that's correct` three. Both are
`complete` turns, where the wording is the entire signal — so half that category was
scoring recall while the generator reported them held out. The guard now folds case and
the roughening tail before comparing; blank messages are exempt, since the empty and
whitespace turns score a behaviour rather than a phrasing.

So **`complete` recall in every row in this file is optimistic**, and no rerun of these
GGUFs recovers it: the contamination is in their training set, not in the eval. Two of
the five `complete` turns are affected. The first model trained after this commit is the
first whose `complete` number means what it says.

### Artifact sizes

| File | On disk | Note |
|---|---|---|
| `qwen2.5-0.5b-instruct-intake-v4-f16.gguf` | 994 MB | conversion target, eval baseline |
| `qwen2.5-0.5b-instruct-intake-v4-q4_k_m.gguf` | 398 MB | `quant size = 373.71 MiB (6.35 BPW)` |

144 of 290 tensors required fallback quantization, identical to v2 and v3 — the 896-wide
tensors still do not divide evenly for every K-quant, so Q4_K_M is really ~6.35 BPW.

Skip recall reads 0.780 against r5's 0.854 on **the same 25 unchanged skip turns** — every
r6 addition golds `skipped_fields: []`. That is run-to-run variation, not a regression; see
the note under r4 on the same effect.

---

## r5 — 108 turns, `property-synonym` added

Same serving setup throughout: llama.cpp b10290, 6 threads, `--parallel 1`,
`--cache-reuse 256`, i7-10750H. All rows `--split all --no-next-question`.

r5 adds six turns testing whether the model maps a client's wording onto a configured
option — `a depot for our trucks`, `cold storage facility`, `an empty parcel to build on`.
Every wording is checked against the generated training vocabulary before it is added, and
a test enforces that on every run, because `property_type_phrasings.json` is regenerated
and could otherwise drift into overlap.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **0.5b-lora-v3-q4km** | **LoRA v3 Q4_K_M** | 108 | 1.000 | 0.874 | 0.927 | 0.899 | **0.842** | 0.897 | 0.854 | 1122 | 1670 |
| 0.5b-lora-v2-q4km-r5 | LoRA v2 Q4_K_M | 108 | 1.000 | 0.810 | 0.988 | 0.890 | 0.593 | 0.535 | 0.480 | 1144 | 1537 |

```bash
python -m pipeline.eval.run --label 0.5b-lora-v2-q4km-r5 --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v2-q4_k_m

python -m pipeline.eval.run --label 0.5b-lora-v3-q4km --split all --no-next-question \
  --base-url http://127.0.0.1:8080/v1 --api-key local \
  --model qwen2.5-0.5b-instruct-intake-v3-q4_k_m
```

v3 is the same recipe as v2 — Qwen2.5-0.5B-Instruct, LoRA on all seven projections, Q4_K_M,
380 MiB on disk, `quant size = 373.71 MiB (6.35 BPW)`. Only the training data changed, and
it was trained on a Colab T4 rather than locally (`pipeline/train/COLAB.md`); the CPU run was
~17 hours for 2250 examples at 2 epochs.

### The defect the new category isolates

| Category | Turns | Field F1 | Value acc | Skip recall |
|---|---|---|---|---|
| `unit-ambiguity` | 12 | 1.000 | 0.667 | — |
| `single-field` | 9 | 0.947 | 0.778 | — |
| `bound-direction` | 8 | 0.941 | 0.375 | — |
| `correction` | 8 | 0.941 | 0.625 | — |
| `multi-field` | 14 | 0.935 | 0.655 | — |
| `previously-skipped` | 8 | 0.800 | 0.750 | 0.750 |
| **`property-synonym`** | **6** | **0.800** | **0.000** | — |
| `skip` | 25 | 0.667 | 1.000 | 0.480 |
| `answer-and-skip` | 5 | 0.571 | 0.500 | 0.500 |
| `complete` | 5 | n/a | n/a | 0.750 |
| `empty-or-noise` | 8 | n/a | n/a | — |

**Field F1 0.800 with value accuracy 0.000.** The model emits the `property_type` key on
almost every turn and gets the value wrong on every one — it echoes the client's noun
("warehouse", "a shop") instead of naming a configured option, so the value is dropped as
unconfigured and the field goes unanswered.

That is the cleanest signal this eval has produced. A floor of exactly zero means any
movement is unambiguous, which is what the v3 training run is measured against.

### v3 closes it

Per category, v2 → v3 (field F1 / value acc / skip recall):

| Category | Turns | Field F1 | Value acc | Skip recall |
|---|---|---|---|---|
| `unit-ambiguity` | 12 | 1.000 → 1.000 | 0.667 → 0.750 | — |
| `single-field` | 9 | 0.947 → **1.000** | 0.778 → **1.000** | — |
| `bound-direction` | 8 | 0.941 → 0.941 | 0.375 → 0.375 | — |
| `correction` | 8 | 0.941 → 0.875 | 0.625 → 0.857 | — |
| `multi-field` | 14 | 0.935 → 0.862 | 0.655 → 0.880 | — |
| `previously-skipped` | 8 | 0.800 → 0.800 | 0.750 → **1.000** | 0.750 → 0.875 |
| **`property-synonym`** | **6** | 0.800 → **0.923** | 0.000 → **1.000** | — |
| `skip` | 25 | 0.667 → 0.667 | 1.000 → 1.000 | 0.480 → **0.800** |
| `answer-and-skip` | 5 | 0.571 → **0.889** | 0.500 → **1.000** | 0.500 → **1.000** |
| `complete` | 5 | n/a | n/a | 0.750 → **1.000** |
| `empty-or-noise` | 8 | n/a | n/a | — |

**All six synonym turns are correct.** Nothing in the code changed: no mapping table, no
prompt edit. The training set was regenerated so half its `property_type` fragments use a
client wording (`pipeline/data/make_phrasings.py`) instead of the literal option, and the model
learned to normalize. Three earlier attempts at this through the prompt — `Should be one
or more of:`, `Must be`, a structural `enum` — each scored 0/5.

**Overall field F1 is flat** (0.890 → 0.899) and that is the honest headline: recall falls
0.061 while precision gains 0.064. v3 emits fewer keys and is right more often about the
ones it emits, which is why value accuracy moves 0.593 → 0.842. `multi-field` and
`correction` lose field F1 while *gaining* value accuracy, the same trade in miniature —
not damage from the over-generic `land` phrasings (`property`, `site`, `ground`), which
would have shown up as a precision *drop*.

**Skip recall 0.480 → 0.854 is above the noise band.** Repeated runs of the same turns have
read 0.707 and 0.480, so anything under ~0.25 is unreadable; this is 0.374 and moves
together with `answer-and-skip` (0.500 → 1.000) and `complete` (0.750 → 1.000). Skip
precision 0.535 → 0.897 rules out the trivial explanation that v3 simply skips more.

`bound-direction` value accuracy is unchanged at 0.375, as expected — nothing in this run
targeted it, and `app/domain/bounds.py` corrects it downstream of the model.

Raw JSON validity holds at 1.000 with `--no-next-question`, so v3 emits the two-key shape
natively. Whether the `next_question` shim in `build_intake_response_schema` can be dropped
is a separate test: it was added because *removing* the field from v2's schema produced 21%
malformed JSON, and this row does not measure that.

### Skip recall on this eval is too noisy to read from one run

Skip recall came in at **0.480** here against **0.707** on r4 — over the *same 25 turns*,
unchanged between revisions. Nothing about them differs; that is run-to-run variation at
temperature 0.1.

It matches the bootstrap measured on r4 (skip recall 95% interval 0.278 wide, on 41 gold
skips), but observing it directly on identical turns is more convincing than the interval
was. **Treat any single-run skip difference below ~0.25 as noise.**

This makes the gate's 0.10 skip-recall threshold unenforceable as written: the metric's own
run-to-run spread is more than twice the margin it is supposed to police. Either score each
model twice and compare means, or the threshold needs revisiting.

---

## r4 — 102 turns, the real questionnaire

Same serving setup as r2: llama.cpp b10290, 6 threads, `--parallel 1`, `--cache-reuse 256`,
i7-10750H. All rows `--split all --no-next-question`. Prompt is 2689 chars, down from 3983,
because the schema now describes four questions instead of six.

| Label | Model | Turns | Raw JSON | Field prec | Field recall | Field F1 | Value acc | Skip prec | Skip recall | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.5b-lora-v2-q4km-r4 | LoRA v2 Q4_K_M | 102 | 0.990 | 0.805 | 0.921 | 0.859 | 0.657 | 0.690 | 0.707 | 1256 | 1689 |

```bash
python -m pipeline.eval.run --label 0.5b-lora-v2-q4km-r4 --split all --no-next-question \
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
python -m pipeline.eval.run --label 0.5b-lora-v2-q4km --split all --no-next-question \
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

## The 7B row: attempted three times, still not measurable

**Attempt on r4.** A one-token probe to the router returned `ok`, so the key, model id and
harness path are all confirmed working. The eval then accepted **5 turns** and returned 402:

```
You have depleted your monthly included credits.
```

The probe passes and the eval does not because an intake prompt is ~950 tokens against the
probe's five. Whatever allowance remains covers trivial calls and nothing real. `7b-router-r4.json`
holds those 5 turns and their raw outputs; it is **not a row** and must not be pasted into
the r4 table.

Earlier attempts on r2 got 6 calls and then 402. Same cause, same abort — which is what
`FATAL_STATUS` exists for, and the reason ~97 turns were not burned against a dead key.

Both times the scored turns were all `single-field`, the easiest category. **Not a
baseline, not comparable to anything.** Two hints worth confirming rather than believing,
consistent across r2 and r4: the 7B over-emits too (field precision 0.500 on r2, 0.625 on
r4, both against single-field gold), and the router shows a long tail a warm local process
does not have — p95 10985 ms against p50 1612 ms on r2, p95 2833 ms against p50 1882 ms on
r4's five.

The thresholds this row has to be judged against are now written down — see
**The gate** in `INTAKE_MODEL_FINETUNE_PLAN.md`. They were set before any 7B number
existed, which is the only time thresholds mean anything.

## What this does not settle

**The gate cannot close.** Everything above compares the 0.5B against itself. There is
still no measurement of the model this would replace, so "good enough" has no referent.
Restoring credits or setting `OPENROUTER_API_KEY` is the only thing in the way, and it
fixes the production outage at the same time.

**And when it does close, it will close on a weak set.** Bootstrapping r4 gives field F1 a
95% interval of 0.129 and skip recall 0.278, because 102 turns carry only 76 gold fields
and 41 gold skips — a third of the turns are deliberately empty. Nothing below ~0.05 field
F1 is enforceable. If the 7B row lands inside a margin, the honest answer is that the
dataset cannot decide, not that the 0.5B passed. Growing the eval to ~400 turns is open
decision 6 for that reason.

## Later rows

| Label | What it establishes |
|---|---|
| `7b-router` | The incumbent, on r2. Everything else is measured against this |
| `0.5b-lora-v2-q4km-holdout` | Whether r2's holdout split agrees with the dev split |
| `0.5b-lora-v3-*` | Whether more `answer-and-skip` data fixes compound refusals |
