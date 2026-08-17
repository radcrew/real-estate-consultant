# Property Image Summarization — Qwen-VL Fine-Tune on Free Compute

Status: proposed, nothing implemented
Scope: new training pipeline + `backend/app/llm/**`, `property_images`, infra
Author: engineering
Date: 2026-08-16
Budget: **$0 standing, near-$0 one-time**

---

## 0. Three corrections to the brief, up front

**Qwen2.5-7B-Instruct cannot read images.** It is a text-only decoder with no vision
encoder. The image-to-text model in that family is the **VL** variant. Everything below
assumes a VL model, and §2 picks a smaller one than the original brief for reasons that
are entirely about the zero-budget constraint.

**SageMaker is out, and not only for the reason previously given.** The earlier version of
this plan argued that a SageMaker *training job* bills per second and so does not conflict
with `AWS_BEDROCK_ARCHITECTURE.md` §21's ban on standing monthly charges. That is true,
but it misses the point: per-second GPU billing is still real money (~$150 to $350 to a
shipped v1), and this platform runs on perpetual free tiers by design. There is no GPU in
the AWS free tier at any tier or duration. SageMaker's free tier is a two-month trial
(§21 of that doc says exactly this). So training moves off AWS entirely.

**The zero-budget path already exists in this repo.** The intake parser is a fine-tuned
Qwen2.5-0.5B served on Lambda CPU for $0 on the perpetual free tier
(`backend/app/llm/providers/qwen_lambda.py`, ECR image `qwen-inference`). This plan is the
same shape one size up: train on free GPU, quantize, serve on CPU. It is not a new pattern,
it is the existing one applied to a vision model.

---

## 1. Goal and scope

### What we are building

A model that takes one listing photo and returns a short, factual, house-style
description of what the photo shows, for commercial real estate specifically.

Input: one image (JPEG/PNG/WebP, already in the `listing-images` Supabase bucket).
Output: 1 to 3 sentences plus a small set of structured tags.

```json
{
  "caption": "Open-plan warehouse floor with roughly 24-foot clear height, two dock-high doors on the rear wall, and full LED high-bay lighting.",
  "space_type": "warehouse",
  "condition": "good",
  "tags": ["dock-high-door", "high-clear-height", "led-lighting", "concrete-floor"]
}
```

### Why fine-tune rather than prompt

A stock VL model describes a photo the way a stock photo caption would ("a large empty
room with a concrete floor"). It does not know that clear height, dock doors, column
spacing, and power service are the facts a commercial tenant cares about, and it will not
hold a consistent voice across 10,000 listings. Those are exactly the two things
supervised fine-tuning is good at: domain vocabulary and output style. It is *not* good at
teaching the model to see something it fundamentally cannot see, so anything requiring
measurement precision (exact square footage, exact clear height) stays out of scope and
comes from the listing record, not the photo.

On a zero budget there is a second reason. A small fine-tuned model that runs on CPU is
free forever; a prompted frontier model is free only until the free-tier rate limits or
data-use terms stop working for you (§3).

### Where the output goes

| Consumer | Use |
|---|---|
| `property_images` rows | new `caption` + `tags` columns, written once per image |
| Listing detail page | per-photo alt text and captions, real accessibility text instead of `""` |
| Search relevance | `tags` folded into the text used for embedding, so "loading dock" matches photos |
| Listing submissions | auto-draft a description for `POST /api/v1/submissions` from the uploaded photos |

### Explicit non-goals

- No real-time, in-request captioning. Captioning happens on upload and on backfill.
- No multi-image reasoning in v1. One image, one caption.
- No claims that are not visible in the photo. The eval in §7 penalizes these hard.
- No paid GPU. If a step needs one, the step is wrong.

---

## 2. Model choice under a zero-budget constraint

The constraint that decides this is not training, it is **serving**. The target is Lambda
CPU inference inside the perpetual free tier (§8), which caps the model at roughly 3B
parameters in 4-bit GGUF. Training then has to fit whatever free GPU exists, which is a
16GB T4. Both point the same direction: smaller than the original 7B brief.

| Candidate | Params | License | Verdict |
|---|---|---|---|
| **`Qwen/Qwen3-VL-4B-Instruct`** | ~4B | Apache-2.0 | **Recommended.** Best quality that still QLoRA-trains on a free T4 and quantizes to ~2.5GB for CPU serving |
| `Qwen/Qwen3-VL-2B-Instruct` | ~2B | Apache-2.0 | Fallback if the 4B is too slow on Lambda CPU. Meaningfully weaker at fine-grained detail |
| `HuggingFaceTB/SmolVLM2-2.2B-Instruct` | 2.2B | Apache-2.0 | Built for on-device. Best CPU latency, mature llama.cpp support. Weakest raw quality |
| `Qwen/Qwen2.5-VL-3B-Instruct` | 3.8B | **Qwen research license** | Technically fine, but the license is not Apache. Do not train on it for a commercial product without legal sign-off |
| `Qwen/Qwen2.5-VL-7B-Instruct` | 8.3B | Apache-2.0 | The original recommendation. QLoRA-trains on a T4 but slowly, and will not serve on Lambda CPU within the free tier. Only if §8 moves to a paid host |

**Verify the exact model ID, the license, and llama.cpp/GGUF support before the first
training run.** Three things have to line up: an Apache-2.0 (or equivalently permissive)
license, a working `transformers` implementation, and a `convert_hf_to_gguf.py` path plus
an `mmproj` vision projector for llama.cpp. The third is the one that silently blocks the
free serving path, and it is worth confirming on day one rather than after training.

Consistency note: the repo already runs a fine-tuned **Qwen2.5-0.5B** for intake parsing
and **Qwen3-32B** on Bedrock for outreach. Staying in the Qwen family keeps one tokenizer
family and one set of chat-template quirks across the platform.

---

## 3. Phase 0: the bake-off that decides whether to fine-tune at all

**Do this before provisioning anything.** Roughly two days of work, and it can save the
entire effort. On a zero budget this phase is itself free.

1. Hand-pick 150 representative listing photos across the space types we actually list
   (warehouse, flex, office, retail, land, exterior, aerial).
2. Have a domain-informed human write the ideal caption for 50 of them. This is the
   eval gold set and it gets reused in §7.
3. Run three zero-shot/few-shot baselines against the same prompt, all on free tiers:
   - **Google AI Studio Gemini free tier** (vision, generous daily quota)
   - **OpenRouter `:free` vision model** (the repo already holds `OPENROUTER_API_KEY`)
   - **The candidate open model off the shelf**, run in a free Kaggle notebook, no training
4. Score all three with the §7 rubric.

**Decision gate.** If a prompted free-tier model with a good system prompt and 3 few-shot
examples already clears the quality bar, **ship that and stop here.**

But read the free tiers' terms before you do. This is the part that is easy to skip:

| Concern | Why it matters here |
|---|---|
| **Data use for model training** | Free tiers of hosted APIs commonly reserve the right to train on your inputs. These are photographs of other people's commercial property, submitted to us. Check the current terms for each provider before sending a single production image |
| **Rate limits** | A few hundred to a few thousand requests per day. Fine for new uploads, not for a 20k backfill in one sitting |
| **No SLA and no stability** | Free endpoints get deprecated, throttled, or withdrawn with no notice. A self-hosted fine-tune cannot be taken away from you |

So the fine-tune is justified by any one of:

- prompted quality plateaus below the bar even after prompt iteration, or
- the free tier's data-use terms are not acceptable for customer photographs, or
- projected volume exceeds free-tier rate limits.

Record the outcome in this document before proceeding to Phase 1.

---

## 4. Data

This is the part that determines success. Everything else is mechanical.

### 4.1 Where images come from

| Source | Volume | Notes |
|---|---|---|
| `public.property_images` | existing catalog | `list_all_image_urls` in `backend/app/repositories/property_images.py` |
| `listing-images` Supabase bucket | user submissions | uploaded via `POST /api/v1/submissions/images` |
| Public CRE listing datasets | as needed to fill gaps | check the license of each before training on it |

### 4.2 Labeling: free-tier teacher distillation plus human correction

We do not have labeled captions and hand-writing 3,000 is not realistic. The workable
path is distillation, and it can be done for $0 if you are willing to trade wall-clock:

1. **Teacher pass, spread over days.** Run a strong hosted vision model on its free tier
   over ~2,000 images with a long, carefully engineered prompt that includes the listing's
   known structured attributes as context. At a few hundred to a thousand requests per
   day this takes 2 to 7 days of unattended running. Write a resumable script with a
   `done` marker per image; you will be restarting it.
   - **Free-tier fallback teacher:** if the terms or limits do not work, run
     `Qwen2.5-VL-7B-Instruct` as the teacher inside a free Kaggle GPU session. About 4s
     per image, so 2,000 images is ~2.5 hours of the weekly quota. Genuinely unlimited and
     genuinely private. The captions are weaker, which means the human pass in step 2 does
     more work.
2. **Human correction.** A reviewer edits or rejects each caption through a throwaway
   internal review page. Budget roughly 20 to 30 seconds per image, so about 12 to 17
   hours for 2,000. Rejections are as valuable as edits: they tell you what the teacher
   gets wrong. **This is the real cost of the project and it does not get cheaper by
   choosing free compute.**
3. **Grounding filter.** Drop any caption asserting a fact that contradicts the listing
   record (says "office build-out" when the listing is raw land). Cheap to automate
   against `properties`, and it removes the worst hallucination class before it becomes
   training signal.

The student learns to produce the teacher's *corrected* output at zero inference cost.
That is the whole economic case.

### 4.3 Target dataset size

Smaller than the SageMaker version, deliberately. Free GPU sessions are time-boxed, and
2,000 well-corrected examples beat 5,000 lightly-reviewed ones for style adaptation.

| Split | Images | Purpose |
|---|---|---|
| train | 1,500 to 2,500 | Enough for style and vocabulary adaptation with QLoRA |
| validation | 200 | Loss curve and early stopping |
| test | 200 | Held out, never seen during any run, including hyperparameter sweeps. 50 of these are the Phase 0 human-gold set |

Stratify all three splits by space type. An eval set that is 70% warehouse tells you
nothing about retail.

### 4.4 On-disk format

One JSONL line per example, images stored as files next to it, in the Qwen chat format:

```json
{
  "messages": [
    {"role": "system", "content": "You describe commercial real estate photographs for a listing platform. State only what is visible. Be specific about features a tenant evaluates."},
    {"role": "user", "content": [
      {"type": "image", "image": "images/prop_8f3a_02.jpg"},
      {"type": "text", "text": "Describe this listing photo."}
    ]},
    {"role": "assistant", "content": "{\"caption\": \"...\", \"space_type\": \"warehouse\", \"condition\": \"good\", \"tags\": [\"dock-high-door\"]}"}
  ]
}
```

The assistant turn is the JSON string, not a nested object. The model is being trained to
emit parseable JSON as text, the same contract `qwen_lambda.py` already relies on for
intake parse.

### 4.5 Storage: Hugging Face Hub, not S3

S3 costs money and adds an AWS dependency to a pipeline that no longer needs one. Use a
**private Hugging Face dataset repo**, which is free, versioned, and is already where the
training code will pull the base model from.

```
hf.co/datasets/<org>/radestate-image-caption   (private)
  v1/
    train.jsonl
    val.jsonl
    test.jsonl
    images/                 # referenced by relative path from the jsonl

hf.co/<org>/radestate-caption-4b               (private)
  checkpoints/<run-id>/     # session-interruption resume target
  merged/                   # merged adapter, fp16
  gguf/                     # Q4_K_M + mmproj, for CPU serving
```

Check the current Hub storage limits for private repos before uploading. At 2,000 images
capped to ~400k pixels each, the dataset is on the order of 200 to 400 MB, which is well
inside any plausible limit. Source images stay in Supabase; the Hub holds only the
resized training copies.

### 4.6 Preprocessing that actually matters

Qwen-VL models use dynamic resolution: token count scales with pixel count, and an
uncapped 4000x3000 listing photo can become several thousand visual tokens on its own.
That is the single biggest driver of memory, and on a 16GB free GPU it is the difference
between training and an OOM on step 3.

**Cap it explicitly.** Set `max_pixels` on the processor to `256 * 28 * 28` (about 200k
pixels, roughly 448x448), which yields on the order of 256 visual tokens per image. This
is half the SageMaker plan's cap, and it is the main concession to free hardware. Then:

- Resize on the CPU during dataset prep, not per-epoch on the GPU. On a time-boxed free
  session, per-epoch CPU resizing wastes GPU minutes you are not getting back.
- Strip EXIF, honor the orientation tag first (rotated photos are a real and silent
  quality bug).
- Deduplicate by perceptual hash. Listing sets repeat the same hero shot constantly, and
  duplicates across the train/test boundary will inflate your eval score.

Run this whole step locally or on a free CPU runner. It needs no GPU.

---

## 5. Training

### 5.1 QLoRA, and specifically which parts to quantize

**Use QLoRA, not plain LoRA.** On a free 16GB T4 this is not close.

| | Plain LoRA, fp16 | **QLoRA, 4-bit nf4** |
|---|---|---|
| 4B base weights | ~8 GB | **~2.5 GB** |
| Left for visual activations | ~5 GB, before optimizer and grad checkpointing | **~11 GB** |
| Pixel cap it affords | forces `128 * 28 * 28`, visibly lossy on floor plans and signage | **`256 * 28 * 28` comfortably, `384 * 28 * 28` if batch stays at 1** |
| Verdict | fits, barely, and spends its headroom on weights | **spends the headroom on image resolution instead** |

The reasoning that matters: for this task, **more visual tokens buy more quality than more
weight precision does.** Captioning a warehouse photo is bottlenecked on whether the model
can resolve the dock door and the light fixtures, not on the fourth decimal place of an
attention weight. QLoRA converts weight precision into resolution, which is the right
trade here.

The quality cost of 4-bit is also small for *this* kind of fine-tune. QLoRA's known
weakness is tasks requiring precise recall of pretrained factual knowledge. We are
teaching vocabulary and output style, which lives in the adapter, not in the frozen base.

**The nuance most QLoRA recipes get wrong on VLMs: do not quantize the vision tower.**

```python
from transformers import BitsAndBytesConfig
import torch

bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.float16,     # fp16, NOT bf16, on a T4 (see 5.3)
    llm_int8_skip_modules=["visual", "lm_head"],   # keep the ViT + merger in fp16
)
```

Three reasons: the ViT is a small fraction of the parameters so quantizing it saves almost
nothing; 4-bit quantization of vision features degrades measurably more than it does for
text; and the merger is a module we want LoRA adapters on, which is cleaner against an
unquantized parent. Confirm the correct module name for the chosen checkpoint, it is
`visual` on Qwen-VL but is not universal.

### 5.2 What to train

| Setting | Value | Reason |
|---|---|---|
| Adapter | LoRA r=16, alpha=32, dropout 0.05 | r=16 for a 2k-example dataset. r=32 is a sweep option, not a default at this data size |
| LLM target modules | `q,k,v,o,gate,up,down` | Standard |
| **Vision tower (ViT)** | **Frozen, unquantized** | The ViT already sees the image fine. What is missing is the language of the domain |
| **Merger / projector** | **LoRA on its linear layers**, not full training | Full-training the merger via `modules_to_save` costs ~600MB of optimizer state in fp32. LoRA on it costs single-digit MB and captures most of the benefit. This is a change from the SageMaker plan, forced by 16GB |
| Precision | fp16 on T4, bf16 only if you land an Ampere or Ada GPU | See 5.3 |
| Optimizer | `paged_adamw_8bit` | Halves optimizer memory and survives the fp16 spikes |

### 5.3 Where the free GPU comes from

| Platform | GPU | Free allowance | Verdict |
|---|---|---|---|
| **Kaggle Notebooks** | T4 16GB (x2) or P100 16GB | **~30 GPU-hours/week**, 12h max session | **Primary.** The most generous and most stable free GPU available. Explicitly select **T4**, not P100 |
| Google Colab, free tier | T4 16GB | unmetered but throttled, sessions die at 4h or less without warning | **Secondary.** Fine for the data-loader smoke test, painful for a real run |
| Lightning AI Studio | L4 24GB | monthly free GPU-hour credit | Worth checking current terms. An L4 is Ada, so bf16 and flash-attention-2 both work, which is a real quality-of-life jump |
| A local GPU, if anyone has one | ≥12GB | free | Best case. No session limits, no queue |
| SageMaker / any cloud GPU | any | **none** | Out. No GPU exists in any AWS free tier |

**Verify the current allowance for whichever you pick.** Free-tier quotas on all of these
change without notice, and last year's numbers are a bad basis for a schedule.

**T4-specific gotchas, all of which will cost you a session if you learn them the hard
way.** The T4 is Turing (sm75):

- **No bf16.** Use `fp16=True` and `bnb_4bit_compute_dtype=torch.float16`. Setting bf16 on
  a T4 either errors or silently falls back and runs slowly.
- fp16 training overflows more readily than bf16. Set `max_grad_norm=0.3`, keep
  `warmup_ratio` at 0.03, and let `prepare_model_for_kbit_training` upcast the LayerNorms
  and the LoRA params to fp32. If loss goes to NaN, this is why.
- **No flash-attention-2** (needs sm80+). Use `attn_implementation="sdpa"`. Installing
  `flash-attn` on a T4 is wasted build time.
- **Avoid P100 on Kaggle.** It is Pascal (sm60), and bitsandbytes 4-bit kernels want sm75
  or newer. The notebook may start and then fail on the first quantized forward pass.

### 5.4 Session limits are the new spot instances

The SageMaker plan checkpointed against spot reclaim. Same problem, different cause: a
free notebook session ends on a timer whether or not your run is done.

- Save a checkpoint every ~100 steps and **push it to the Hub**, not just to local disk.
  Kaggle and Colab both delete the local filesystem when the session ends.
- Have the entrypoint look for the newest checkpoint on the Hub and resume from it. Then a
  killed session costs you 100 steps, not the run.
- Keep total run time under the session cap on purpose. See 5.6.

### 5.5 Hyperparameters

```python
model_id            = "Qwen/Qwen3-VL-4B-Instruct"   # verify ID and license first (§2)
epochs              = 2                              # 3 is a sweep, not a default at 2k examples
per_device_bs       = 1
grad_accum          = 8                              # effective batch 8
learning_rate       = 1e-4                           # LoRA wants ~10x a full fine-tune's LR
lr_scheduler_type   = "cosine"
warmup_ratio        = 0.03
max_grad_norm       = 0.3                            # fp16 safety
weight_decay        = 0.0
lora_r, lora_alpha  = 16, 32
lora_dropout        = 0.05
max_pixels          = 256 * 28 * 28
gradient_checkpointing = True
optim               = "paged_adamw_8bit"
fp16                = True                           # bf16=False on T4
attn_implementation = "sdpa"
save_steps          = 100
push_to_hub         = True
```

Two things that are not hyperparameters but decide whether the run is worth anything:

- **`train.py` must mask the loss on prompt tokens and compute it on assistant tokens
  only.** Getting this wrong is the single most common silent failure in VLM SFT: the run
  completes, the loss looks fine, and the model has learned to parrot prompts. Assert on
  20 examples that only assistant tokens carry loss, before the first full run.
- **Validate the data loader on CPU first**, on 20 examples. A shape mismatch discovered
  40 minutes into a session is 40 minutes of a weekly quota you do not get back.

### 5.6 Expected run time

2,000 examples, 2 epochs, ~600 tokens each, 4B model 4-bit on one T4 with gradient
checkpointing: roughly **3 to 5 hours**, plus eval. That fits inside one Kaggle session
with margin, which is the whole reason the dataset and pixel cap were sized down.

Budget 3 real runs plus false starts, so 2 to 3 weeks of Kaggle quota if you are running
one experiment at a time. **Wall-clock, not money, is what free costs you.**

---

## 6. Repository integration

`training/qwen-vl-caption/` already exists and is empty. Proposed contents:

```
training/qwen-vl-caption/
  README.md
  pyproject.toml           # own venv, not a pnpm workspace member
  prepare_dataset.py       # Supabase -> resize/dedupe/split -> HF Hub  (CPU, local)
  teacher_label.py         # free-tier teacher pass, resumable (§4.2)   (CPU, local)
  train.py                 # notebook entrypoint, Hub checkpoint/resume (free GPU)
  evaluate.py              # §7 rubric                                   (CPU + free API)
  export_gguf.py           # merge adapter -> fp16 -> Q4_K_M + mmproj    (CPU, local)
  notebooks/
    kaggle_train.ipynb     # thin wrapper: clone repo, pip install, call train.py
```

Keeping the logic in `.py` files and the notebook as a thin wrapper matters more here than
usual. Notebooks are not reviewable in a diff, and this code will be re-run across many
sessions by whoever has quota left that week.

Its own venv and `pyproject.toml`, matching how `backend/`, `services/mcp/`, and
`services/ingestion/` each carry their own.

The inference-side client mirrors the existing provider shape: `qwen_lambda.py` is the
template (IAM invoke, circuit breaker, retry-then-degrade, no cross-family fallback). A new
`vision_caption.py` provider next to it, wired through `routing.py`, keeps the pattern.

Schema change: `property_images` gains `caption text`, `tags text[]`, `caption_model text`,
`caption_generated_at timestamptz`. Recording the model version per row is what lets you
re-caption selectively after run 2 instead of re-running everything.

---

## 7. Evaluation

**BLEU, ROUGE, and CIDEr are close to useless here.** They reward n-gram overlap with one
reference caption, and a correct caption phrased differently scores badly. Use them only
as a cheap regression tripwire between runs, never as the quality bar.

The real rubric, scored by an LLM judge on the 200-image test set, plus a full human pass
on the 50 gold images. The judge runs on a free tier, and 200 images is well inside any
free daily quota.

| Dimension | Question | Weight |
|---|---|---|
| **Groundedness** | Is every asserted fact visible in the photo? Any hallucination fails the item outright | 40% |
| Specificity | Does it name features a tenant evaluates, or is it generic photo-caption filler? | 25% |
| Style | Does it match house voice, length, and register? | 15% |
| Schema validity | Does it parse as JSON, with `space_type` from the enum? | 10% |
| Tag precision | Are the emitted tags correct, and is recall reasonable? | 10% |

Groundedness carries the most weight because a hallucinated "recently renovated office
build-out" on a listing page is a factual claim we published about someone's property.
That is a legal and trust problem, not a quality metric.

Gates:

- **Ship gate:** beats the Phase 0 prompted baseline on the weighted score, and has a
  hallucination rate at or below 2% on the gold 50.
- **Regression gate:** any later run must not lose more than 1 point against the frozen
  test set.
- **Quantization gate, new and easy to forget:** re-run the full eval on the **Q4_K_M GGUF
  build**, not just on the fp16 merged model. Serving quantization can cost real quality,
  and the model you ship is the quantized one. If Q4_K_M fails the gate, try Q5_K_M and
  accept the larger Lambda image.

Run the human pass on the gold 50 for every candidate that clears the automated gate. The
judge and the student share failure modes, and the judge will forgive things a person
will not.

---

## 8. Serving for $0

Fine-tuning on free compute does not by itself make serving free. This section is where
the standing-cost rule in `AWS_BEDROCK_ARCHITECTURE.md` §21 actually binds.

| Option | Standing cost | Latency | Fit |
|---|---|---|---|
| **Free GPU notebook, batch** | **$0** | hours, manual | **Best for the 20k backfill.** Run captioning in the same Kaggle session, write results straight to Supabase |
| **Lambda CPU + llama.cpp GGUF** | **$0** within the free tier | 30 to 60s per image | **Best for new uploads.** Exactly the `qwen-inference` pattern already deployed for the 0.5B intake model |
| GitHub Actions, scheduled CPU batch | $0 to the 2,000 min/mo private-repo allowance | ~90s per image | Viable alternative to Lambda. The repo already runs scheduled workflows |
| Modal / similar, free monthly credit | $0 up to the credit, then real money | ~1s warm | Fastest and least fiddly, but it is a credit, not a free tier. It runs out |
| SageMaker Async Inference at `min_capacity=0` | $0 idle, but **paid per invocation-second on GPU** | 1 to 3 min cold | The previous plan's recommendation. Not free, and no longer needed |
| Real-time endpoint 24/7 | ~$1,100/mo | ~1s | **Rejected.** Exactly the standing cost §21 forbids |

**Recommendation: Lambda CPU for the live path, free GPU notebook for the backfill.**

### 8.1 The Lambda free-tier math, which decides the model size

The perpetual free tier is 1M requests and **400,000 GB-seconds per month**. At the 10GB
memory setting a captioning function needs:

```
400,000 GB-s / 10 GB = 40,000 function-seconds/month
```

| Per-image latency | Images/month free | Cost per image beyond it |
|---|---|---|
| 30s (2B, Q4_K_M) | ~1,300 | ~$0.005 |
| 60s (4B, Q4_K_M) | ~660 | ~$0.010 |

So: **the 4B model is free up to roughly 650 new uploads per month, the 2B up to about
1,300.** Above that, stop invoking Lambda per upload and let the queue accumulate for a
nightly free-GPU batch instead. Answering open question 4 (actual monthly image volume)
is what picks between the 4B and the 2B, and it should be answered before Phase 1.

Wire it as: upload writes the row with `caption IS NULL`, enqueues to the existing SQS FIFO
pattern from `AWS_BEDROCK_ARCHITECTURE.md` §14.1, a worker invokes the captioning Lambda,
the result writes `caption` and `tags` back to `property_images`. SQS is free to 1M
messages/month, so the queue adds nothing.

### 8.2 The GGUF export, which is the actual risk

`export_gguf.py` merges the LoRA adapter into fp16, converts with
`convert_hf_to_gguf.py`, quantizes to Q4_K_M, and produces the separate **`mmproj`** file
holding the vision encoder. llama.cpp's multimodal support needs both.

**Confirm on day one that llama.cpp supports the chosen checkpoint's vision architecture
and can produce its `mmproj`.** Support lands per model family and lags new releases. If it
does not exist for the model you picked, the free serving path collapses and you are back
to a paid host, which invalidates this whole plan. This is the single check that most
deserves to happen before any other work.

---

## 9. Cost

| Line item | SageMaker plan | **This plan** |
|---|---|---|
| Teacher labeling | $40 to $120 (Bedrock) | **$0** (free-tier API, or local 7B on free GPU) |
| Training, real runs | $10 to $20 | **$0** (Kaggle) |
| Debug runs and warm-pool idle | $50 to $150 | **$0**, paid in weekly quota instead |
| Dataset and checkpoint storage | few $/mo (S3) | **$0** (HF Hub private repo) |
| Backfill, 20k images | $15 to $40 | **$0** (free GPU batch) |
| Ongoing inference | low $/mo | **$0** to ~650-1,300 images/mo (Lambda free tier) |
| **Total AWS/API spend to a shipped v1** | **$150 to $350** | **$0** |
| Human correction, ~15 hours | internal time | **internal time, unchanged** |
| Engineering time | ~1 week | **~1.5 to 2 weeks** |

**What free actually costs.** It is not nothing, it is just not billed:

- **Wall-clock.** 30 GPU-hours a week is a hard ceiling. Three training runs with false
  starts is 2 to 3 weeks, against 3 to 4 days on a paid GPU.
- **Engineering time.** Checkpoint/resume across dying sessions, the GGUF export path, and
  Lambda packaging are all work that a paid endpoint would have absorbed. Call it an extra
  3 to 5 days.
- **A hard model-size ceiling.** The free serving tier caps the model at ~4B. If eval says
  the task needs 7B, no amount of cleverness in this plan gets you there for $0, and the
  honest answer is to revisit §8 with a budget.
- **Data-use terms on free API tiers**, if you use a hosted teacher (§3).

The one line that does not change is human correction. It was the dominant real cost in
the paid plan and it is the dominant real cost here.

---

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **llama.cpp has no `mmproj` path for the chosen model** | Kills the $0 serving path entirely | Verify on day one, before any training (§8.2). Fall back to SmolVLM2, which has the most mature llama.cpp support |
| **Free GPU quota exhausted mid-experiment** | Days of delay | Two platforms configured (Kaggle + Colab), Hub checkpoints so any session can resume any run |
| **Session dies before the first checkpoint** | Lost hours | `save_steps=100` with Hub push, and never run a session without confirming step-100 upload succeeded |
| **fp16 NaN on T4** | Run silently produces garbage | `max_grad_norm=0.3`, `paged_adamw_8bit`, watch the first 50 steps of loss before walking away |
| **4-bit quantization costs more quality than expected** | Ship gate fails | Eval the GGUF build, not the fp16 merge (§7). Q5_K_M as the fallback |
| **4B is too slow on Lambda CPU** | Blows the free tier | Measure real cold and warm latency in Phase 1 with the *stock* model, before training anything. Drop to 2B if needed |
| **Free-tier teacher trains on our customers' photos** | Legal and trust | Read the current terms in Phase 0. Local 7B teacher on free GPU if they are not acceptable |
| **Hallucinated features published on listings** | Legal and trust | 40% eval weight, grounding filter (§4.2), 2% ship gate, human review path for submissions |
| **Loss masking bug** | Silently trains garbage | Assert on 20 examples that only assistant tokens carry loss, before the first full run |
| **Test set contamination via duplicate photos** | Inflated scores, bad ship decision | Perceptual-hash dedupe *before* splitting (§4.6) |
| **Fine-tune does not beat the prompted baseline** | Sunk time | This is what Phase 0 exists to find out cheaply |
| **Overfitting on 2k examples** | Repetitive, templated captions | Early stopping on val loss, and read 20 actual outputs per run. Val loss will not show you templating |

---

## 11. Phases

| Phase | Work | Exit criterion |
|---|---|---|
| **0. Bake-off** | 150-image sample, 50 human-gold captions, 3 free-tier prompted baselines scored, free-tier terms read | A written decision: fine-tune, or ship the prompted model and stop |
| **1. Feasibility** | **llama.cpp `mmproj` check for the chosen model**, stock-model latency on Lambda CPU, Kaggle account and quota confirmed, version-matrix notebook | The stock model captions one image on Lambda CPU inside the free-tier budget. **If this fails, stop and re-scope, do not proceed** |
| **2. Data** | Teacher pass (days, unattended), human correction, grounding filter, dedupe, split, push to HF Hub | 1,500+ corrected training examples on the Hub, stratified splits |
| **3. Training** | `train.py`, CPU-validate the loader, one real Kaggle run with Hub checkpointing | A trained adapter, and the loss mask verified correct |
| **4. Eval** | `evaluate.py`, free-tier judge, human pass on the gold 50, **eval the GGUF build** | Beats the Phase 0 baseline, hallucination rate at or below 2%, quantized model still passes |
| **5. Iterate** | r=32, 3 epochs, higher `max_pixels`, unfreeze the vision tower | Best run selected and frozen |
| **6. Serve** | Free-GPU backfill batch, Lambda container + SQS worker, `property_images` columns, backend provider | Captions on live listings, $0 standing cost |

Phase 1 moved ahead of data collection on purpose. The paid plan could afford to discover
a serving problem late; this one cannot, because the entire justification is that serving
is free. Prove that first.

Phases 0 through 4 are the commitment. Phase 5 is optional and demand-driven. Phase 6
should not start until Phase 4 passes, since a model that does not clear the gate should
not be plumbed into the product at all.

---

## 12. Open questions

1. Who does the human correction pass in Phase 2, and do they have the CRE domain
   knowledge to catch a teacher model calling flex space a warehouse?
2. Is the caption a listing-facing published claim, or internal search metadata only? The
   answer changes the hallucination tolerance by an order of magnitude.
3. **What is the actual image volume per month?** This is now the question that picks the
   model size. Under ~650/month the 4B serves free on Lambda; above that it is the 2B, or
   a nightly batch, or a bill (§8.1). Answer before Phase 1.
4. Does llama.cpp currently support the chosen model's vision tower and produce an
   `mmproj`? Phase 1's gating check (§8.2).
5. Is a free-tier hosted API acceptable for teacher labeling given its data-use terms, or
   does the teacher have to be the local 7B on free GPU?
6. Does anyone on the team have a local GPU with 12GB or more? It removes the session-limit
   problem entirely and would cut the timeline by a week.
