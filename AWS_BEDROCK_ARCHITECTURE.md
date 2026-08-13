# LLM Platform Architecture — Self-hosted Qwen + Bedrock

Status: proposal / not yet implemented
Scope: `backend/**`, deployment and infrastructure
Author: engineering

> Supersedes the earlier Bedrock-only and SageMaker-GPU drafts. Those assumed a ~7B model on an
> always-on GPU; the actual model is **Qwen 0.5B, fine-tuned for one task**, which runs on CPU
> and changes the cost and hosting picture entirely. Filename kept so existing links resolve.

---

## 0. The design in one table

| Workload | Runs on | Why |
|---|---|---|
| **Criteria extraction** from free-text user input (intake parse) | **Qwen 0.5B on AWS Lambda (CPU)** | Our fine-tune, narrow task. 0.5B needs no GPU — it fits in Lambda's memory and runs on Lambda's CPU. Scale-to-zero, plausibly inside the perpetual free tier (§5) |
| **Embeddings** | **Bedrock** `cohere.embed-english-v3` | Managed, per-token, batches ~96 per call. Also a 384 → 1024-dim quality upgrade |
| **General chat** — opening question, fit explanation, outreach drafts | **Bedrock** `anthropic.claude-sonnet-5` | Open-ended generation the 0.5B fine-tune was never trained for |
| **Fallback** when the Qwen function fails | **Bedrock** | A fine-tune has no SLA. Same IAM, same region |
| **Bulk / backfill** embedding jobs | **Bedrock batch inference** (S3 in/out) | ~50% cheaper, separate quota pool |
| **Guardrails** on input/output | **Bedrock `ApplyGuardrail`** | Runs standalone against any model's text, including Qwen's (verify current support) |

**Not using:** SageMaker (§5.6), GPU instances, provisioned throughput. None are needed for a
0.5B CPU model.

### The picture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          REAL ESTATE CONSULTANT                              │
│                                                                              │
│   ┌────────────┐            ┌──────────────────────────────────┐             │
│   │  Next.js   │───────────▶│        FastAPI backend           │             │
│   │  frontend  │            │      providers/routing.py        │             │
│   └────────────┘            └────────┬────────────────┬────────┘             │
│                                      │                │                      │
│                 ┌────────────────────┘                └───────────┐          │
│                 ▼                                                 ▼          │
│   ┌─────────────────────────────┐              ┌───────────────────────────┐ │
│   │      A W S   L A M B D A    │              │      B E D R O C K        │ │
│   │  ┌───────────────────────┐  │              │ ┌───────────────────────┐ │ │
│   │  │ qwen-inference        │  │              │ │ cohere.embed-v3       │ │ │
│   │  │ Qwen 0.5B, CPU        │  │              │ │ embeddings            │ │ │
│   │  │ container image (ECR) │  │              │ ├───────────────────────┤ │ │
│   │  │ grammar-constrained   │  │              │ │ claude-sonnet-5       │ │ │
│   │  │ JSON                  │  │              │ │ general chat +        │ │ │
│   │  └───────────────────────┘  │              │ │ fallback              │ │ │
│   │                             │              │ ├───────────────────────┤ │ │
│   │  ONE task: criteria         │              │ │ Guardrails            │ │ │
│   │  extraction                 │              │ ├───────────────────────┤ │ │
│   │                             │              │ │ Batch inference       │ │ │
│   │  scales to zero · ~$0       │              │ └───────────────────────┘ │ │
│   └─────────────────────────────┘              │ managed · per-token       │ │
│                                                └───────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Two tiers

| Tier | What | When |
|---|---|---|
| **Part I** (§1–§10) | Routing + the Qwen Lambda + Bedrock providers, behind the existing protocol seam | Now |
| **Part II** (§11–§21) | Scale concerns: runtime on AWS, queueing, vector search, caching | When traffic justifies it |

---

# Part I — Providers and routing

## 1. Goals

- Serve the fine-tuned Qwen 0.5B for criteria extraction, on CPU, at effectively no cost.
- Use Bedrock for embeddings, general chat, fallback, batch, and guardrails.
- Route **per call site**, so each of the four LLM paths moves independently.
- Keep OpenRouter/HF working as a rollback target throughout.

Non-goals: streaming, agentic tool loops, replacing Supabase, any GPU.

## 2. Current state

```
app/llm/{intake,fit,outreach}/service.py
        ├── generate_structured_output()  ── providers/chat.py ───────┐
        └── embed()                       ── providers/embeddings.py ─┤
                                        resolve_*_provider(config)    │
                                    ┌─────────────────┴──────────┐    │
                                    ▼                            ▼    │
                          OpenRouterProvider            HuggingFaceProvider
                          (llama-3.1-8b-instruct)       (all-MiniLM-L6-v2, 384-dim)
```

Two protocols, `ChatProvider` and `EmbeddingsProvider` (`providers/base.py`), and nothing above
the seam touches a vendor SDK.

**One structural gap:** `resolve_chat_provider()` returns a *single* provider for all chat. With
Qwen serving exactly one of four paths, per-task routing is required. That is §3.

## 3. Model routing — the centerpiece

### 3.1 The routing table

The fine-tune covers **one** task. Everything else needs a general model.

| Call site | Code | Route | Why |
|---|---|---|---|
| **Intake parse** | `llm/intake/service.py:62` | **Qwen 0.5B (Lambda)** | Exactly what it was fine-tuned for. Highest volume, narrow, structured |
| Opening question | `llm/intake/service.py:100` | Bedrock Claude | Open-ended phrasing; also highly cacheable (§16), so volume is low |
| Fit explanation | `llm/fit/service.py` | Bedrock Claude | Reasoning + prose |
| Outreach draft | `llm/outreach/service.py` | Bedrock Claude | Generative writing |
| Embeddings | `services/similar_listings.py:55` | Bedrock Cohere v3 | §6.1 |

A 0.5B fine-tuned on one task can beat a general 8B *at that task* while being ~16× smaller —
that's the whole point. It will not transfer to the other three, and asking it to is the fastest
way to conclude the fine-tune "doesn't work."

> Cost note: if Claude Sonnet 5 is more than those three paths warrant, route them to
> `anthropic.claude-haiku-4-5`, or leave them on OpenRouter until the Qwen path is proven. The
> routing table is per-path env vars — this is a config decision, not a code one.

### 3.2 Implementation

```python
# app/llm/providers/routing.py  (new)
class LlmTask(StrEnum):
    INTAKE_PARSE     = "intake_parse"
    OPENING_QUESTION = "opening_question"
    FIT_EXPLANATION  = "fit_explanation"
    OUTREACH_DRAFT   = "outreach_draft"

def resolve_chat_provider(*, task: LlmTask | None, config: Settings) -> ChatProvider:
    """Route by task, falling back to `llm_route_default`, then to key-presence order."""
```

One env var per task, so routing changes are a redeploy and never a code change:

```python
llm_route_intake_parse:     str = "qwen"          # qwen | bedrock | openrouter | huggingface
llm_route_opening_question: str = "bedrock"
llm_route_fit_explanation:  str = "bedrock"
llm_route_outreach_draft:   str = "bedrock"
llm_route_default:          str = "bedrock"
llm_route_fallback:         str = "bedrock"       # §3.3
```

Call sites gain one keyword argument:

```python
parsed_output = await generate_structured_output(
    messages=[...], response_format=LlmParseModelOutput,
    temperature=0.1, max_tokens=800,
    task=LlmTask.INTAKE_PARSE,          # ← new
)
```

Four one-line edits. `task` defaults to `None` → `llm_route_default`, so an un-annotated call
site still works.

### 3.3 Fallback — explicit, bounded, logged

Fallback is correct here, because the primary is a self-hosted model with no vendor SLA — and a
0.5B has less headroom on unusual input than a large model, so the path will actually be used.

- Trigger on **infrastructure failure only** — Lambda invoke error, timeout, throttle,
  circuit-breaker open. **Never** on a validation failure or refusal; that just buys the same bad
  answer twice.
- One attempt, no chaining.
- Log `fallback_used=true` with the reason and alarm on the rate. A silent fallback running for a
  week is how you discover the Qwen function has been broken since Tuesday.
- Circuit breaker in ElastiCache (or in-process at low scale) so a dead function stops being
  retried per request.

## 4. Target architecture

```
┌─────────────────────────── FastAPI backend ──────────────────────────────────┐
│                                                                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────────┐  │
│  │ intake/       │ │ fit/          │ │ outreach/     │ │ services/        │  │
│  │ service.py    │ │ service.py    │ │ service.py    │ │ similar_listings │  │
│  └───────┬───────┘ └───────┬───────┘ └───────┬───────┘ └────────┬─────────┘  │
│  task=INTAKE_PARSE  task=FIT_       task=OUTREACH_               │           │
│  task=OPENING_Q     EXPLANATION     DRAFT                        │           │
│          └─────────────────┴────────────────┘                    │           │
│                            ▼                                     ▼           │
│         ┌──────────────────────────────────┐   ┌────────────────────────────┐│
│         │ providers/chat.py                │   │ providers/embeddings.py    ││
│         │ providers/routing.py             │   └──────────────┬─────────────┘│
│         │  • per-task table       §3.1     │                  │              │
│         │  • fallback on infra error §3.3  │                  │              │
│         │  • circuit breaker               │                  │              │
│         └────────────────┬─────────────────┘                  │              │
└──────────────────────────┼────────────────────────────────────┼──────────────┘
        ┌─────────┬────────┴────────┬──────────┐                │
        ▼         ▼                 ▼          ▼                ▼
 ┌────────────┐┌────────────┐┌───────────┐┌───────────┐ ┌──────────────────┐
 │ QwenLambda ││ BedrockChat││OpenRouter ││HuggingFace│ │ BedrockEmbeddings│
 │ Provider   ││ Provider   ││(rollback) ││(rollback) │ │ Provider         │
 ├────────────┤├────────────┤└───────────┘└───────────┘ ├──────────────────┤
 │ boto3      ││ anthropic  │                           │ boto3            │
 │ lambda     ││ SDK        │                           │ bedrock-runtime  │
 │ .invoke()  ││ (Mantle)   │                           │ InvokeModel      │
 ├────────────┤├────────────┤                           ├──────────────────┤
 │ Qwen 0.5B  ││ anthropic. │                           │ cohere.embed-    │
 │ CPU, GGUF  ││ claude-    │                           │ english-v3       │
 │ GBNF JSON  ││ sonnet-5   │                           │ 1024-dim         │
 └────────────┘└────────────┘                           └──────────────────┘
  INTAKE PARSE  EVERYTHING ELSE                            EMBEDDINGS
                + FALLBACK
```

### New/changed files

| File | Change |
|---|---|
| `app/llm/providers/routing.py` | **new** — `LlmTask`, per-task resolution, fallback + circuit breaker |
| `app/llm/providers/qwen_lambda.py` | **new** — `QwenLambdaProvider` |
| `app/llm/providers/bedrock_chat.py` | **new** — `BedrockChatProvider` |
| `app/llm/providers/bedrock_embeddings.py` | **new** — `BedrockEmbeddingsProvider` |
| `app/llm/providers/chat.py` | `generate_structured_output(..., task=None)` delegates to routing |
| `app/llm/providers/exceptions.py` | `raise_qwen_*` and `raise_bedrock_*` mappers |
| `app/core/config.py` | Qwen + Bedrock + routing settings |
| `app/llm/{intake,fit,outreach}/service.py` | one `task=` kwarg each (4 lines) |
| `infra/qwen-lambda/` | **new** — Dockerfile, handler, model artifact |
| `pyproject.toml` / `requirements.txt` | `anthropic[bedrock]`, `boto3` |
| `tests/llm/providers/test_{qwen_lambda,bedrock_chat,bedrock_embeddings,routing}.py` | **new** |

## 5. Hosting Qwen 0.5B on Lambda

### 5.1 Why CPU, and why Lambda

Qwen 0.5B is roughly 1 GB at bf16, ~500 MB at int8, ~350 MB at 4-bit. It fits in ordinary RAM,
and criteria extraction emits only ~100–200 output tokens. That is a **CPU workload measured in
seconds**, not a GPU workload.

Once the GPU is gone, the requirement becomes: run occasionally, cost nothing when idle, need no
cluster. That is Lambda.

> **This reverses the "Lambda is wrong for the chat path" advice in §13**, and the reason matters.
> That advice was about Lambda sitting *blocked on a network call to a remote model*, billing
> wall-clock for idle waiting. Here the CPU work **is** the request, so paying for that time is
> exactly right.

### 5.2 Container image and runtime

Lambda container images support up to 10 GB, so the weights ship **inside the image** — no
cold-start download from S3, no EFS mount to manage.

```
infra/qwen-lambda/
├── Dockerfile          # FROM public.ecr.aws/lambda/python:3.12
├── handler.py          # load once at module scope, reuse across warm invocations
├── model/
│   └── qwen-0.5b-ft.Q8_0.gguf
└── schemas/            # pre-compiled GBNF grammars per output schema
```

**Runtime: `llama.cpp` (via `llama-cpp-python`) with a GGUF quant.** Chosen over Transformers or
ONNX Runtime for three reasons: the smallest image and fastest init, `mmap` weight loading (fast
cold start), and **native GBNF grammar support**, which is what §5.3 depends on. ONNX Runtime is
a reasonable alternative if you already have an ONNX export; Transformers + PyTorch is the
heaviest option and the slowest to initialise.

Load the model **at module scope**, not inside the handler, so warm invocations reuse it.

### 5.3 Constrained JSON output — non-negotiable

Small models are markedly worse at reliably emitting valid JSON. This is the single biggest risk
in the whole plan, and it has a clean solution: **constrain the decoder** so invalid output is
impossible rather than unlikely.

```
Pydantic model  ──▶  JSON Schema  ──▶  GBNF grammar  ──▶  llama.cpp sampler
(LlmParseModelOutput)   (normalised)     (pre-compiled)     (cannot emit invalid tokens)
```

- Generate the grammar from `response_format.model_json_schema()` at **build time** and bake it
  into the image — grammar compilation is not free, and the schema only changes when you deploy.
- Normalise the schema first: force `additionalProperties: false`, drop unsupported keywords.
  Same helper the Bedrock path uses (§6.2), unit-tested against `LlmParseModelOutput`.
- Still call `model_validate_json` on the result. The grammar guarantees *shape*, not *sense* —
  a required field can still come back empty.
- On `ValidationError`: one retry, then fall back (§3.3).

Do not ship this path relying on prompt instructions alone. It will work in testing and fail in
production on the inputs that matter.

### 5.4 Memory, CPU, and cold starts

Lambda allocates CPU **in proportion to memory** — ~1 vCPU at 1,769 MB, ~2 at 3,008 MB, up to 6
at 10,240 MB. More memory means faster inference, which means shorter duration, which can make a
larger setting **cheaper overall**. Do not guess: run AWS Lambda Power Tuning across
1,769 / 3,008 / 5,120 MB with a representative intake prompt and pick from the measured
cost-vs-latency curve. Start at 3,008 MB.

**Cold start** is container init plus model load — expect a few seconds with `mmap`. Two cheap
mitigations, in order:

1. **EventBridge ping every 5 minutes** keeps one environment warm. ~8,600 invocations/month,
   comfortably inside the free tier. This is the recommended default.
2. Provisioned concurrency eliminates cold starts entirely but **bills continuously** — it defeats
   the reason we chose Lambda. Only if p99 latency becomes a stated product requirement.

Also set: timeout ~30 s, and **reserved concurrency** as a cost blast-radius cap.

### 5.5 Provider implementation

```python
class QwenLambdaProvider:
    def __init__(self, *, settings: Settings, client=None):
        self.settings = settings
        self._client = client or boto3.client("lambda", region_name=settings.aws_region)

    async def generate_structured_output(self, *, messages, response_format, temperature, max_tokens):
        payload = {
            "messages": messages,
            "schema_name": response_format.__name__,   # selects the pre-built grammar
            "max_tokens": max_tokens,
            "temperature": temperature,                # ✅ Qwen honours this
        }
        raw = await anyio.to_thread.run_sync(partial(self._invoke, payload))
        return response_format.model_validate_json(raw["text"])
```

Notes:

- **`temperature` works here.** Qwen honours sampling parameters, so the existing `0.1` passes
  through unchanged — unlike the Bedrock/Claude path (§6.2(b)), which rejects it. This asymmetry
  is precisely why routing is per-task.
- **`max_tokens=800` stays valid.** No thinking budget to account for.
- boto3 is synchronous → `anyio.to_thread.run_sync` (available via Starlette, no new dependency).
- Invoke over IAM (`lambda:InvokeFunction`) rather than a Function URL — no public endpoint, no
  separate auth to manage.
- Send `schema_name`, not the full schema: grammars are pre-compiled in the image (§5.3).

### 5.6 Hosting alternatives — including "can SageMaker be free?"

| Option | Cost | Verdict |
|---|---|---|
| **Lambda container image** | **Plausibly $0** — the free tier (1M requests + 400,000 GB-s) is **perpetual**. At ~3 GB × ~2 s = 6 GB-s per call, that's roughly **65,000 free calls/month**, every month. Beyond it, ~$0.0001/call | **Recommended** |
| **SageMaker Serverless Inference** | Free tier is a **time-limited trial for new accounts** (historically ~2 months). After it expires: per GB-second + per request, forever | Legitimate, never permanently free. Less container work, a few dollars/month |
| **Model in-process on Fargate** | **$0 marginal** — it runs inside API containers you already pay for | **The endgame** once off Vercel (§13) |
| SageMaker real-time endpoint | ~$30+/month minimum, always on | Unnecessary |
| Any GPU instance | $500+/month | Wrong by two orders of magnitude for 0.5B |

**Direct answer on SageMaker:** not permanently free. The distinction that matters is not the
per-unit price — those are comparable — but that **Lambda's free allowance renews monthly and
SageMaker's expires.** Confirm current terms in the console; AWS revised free-tier structures in
2025.

**The honest asterisk on "$0":** ECR image storage (~$0.10/GB/month for a 1–2 GB image) and
CloudWatch Logs ingestion are billed regardless. Cents, not dollars — but not literally zero.

**The trajectory worth planning for:** Lambda now, because you are on Vercel and cannot host a
model there. Once the API tier moves to Fargate (§13), the cleanest answer is to **drop the
separate service and load the 0.5B directly into the API container** — no network hop, no second
deployment, no marginal cost. That option exists only because the model is small; it is one of
the better consequences of the 0.5B choice.

## 6. Bedrock — everything else

### 6.1 Embeddings — `cohere.embed-english-v3`

`bedrock-runtime` `InvokeModel`, versioned model IDs.

| Candidate | Dims | Batch/call | Fit |
|---|---|---|---|
| **`cohere.embed-english-v3`** | 1024 | ~96 | ✅ recommended |
| `cohere.embed-multilingual-v3` | 1024 | ~96 | ✅ if non-English listings appear |
| `amazon.titan-embed-text-v2:0` | 1024 (256/512) | **1** | ⚠️ needs fan-out |

`find_similar_listings` embeds a seed plus up to 100 candidates in one call
(`similar_listings.py:52-55`) — Cohere serves that in one or two round-trips; Titan would need
101 sequential calls. Also a straight quality upgrade over today's 384-dim `all-MiniLM-L6-v2`.

Implementation: chunk to `bedrock_embedding_batch_size` (default 96); **preserve order** —
`similar_listings.py:61` zips vectors positionally against candidate rows, so reordering silently
mis-scores every listing; assert `len(vectors) == len(texts)`.

Verify body shapes against current docs (model-specific and versioned):

```
Cohere v3 → {"texts": [...], "input_type": "search_document"} → {"embeddings": [[...], ...]}
```

### 6.2 General chat and fallback — `anthropic.claude-sonnet-5`

Via `AnthropicBedrockMantle` (Messages API). Bedrock IDs on this path are first-party IDs with an
`anthropic.` prefix and **no** date suffix, `-v1:0`, or inference-profile prefix:

```python
from anthropic import AnthropicBedrockMantle
client = AnthropicBedrockMantle(aws_region=settings.aws_region)   # region required, no default
```

Four adaptations, all confined to this provider:

**(a) `system` is a top-level parameter**, not a message. Callers pass
`[{"role": "system", ...}, {"role": "user", ...}]` (`intake/service.py:62-70`) — split it out.

**(b) `temperature` must be dropped.** Claude Opus 5 / 4.7+ reject `temperature`/`top_p`/`top_k`
with a **400**; Sonnet 5 rejects non-default values. Keep it in the protocol (Qwen, OpenRouter and
HF all use it) but this provider ignores it, documented in the docstring.

**(c) Structured output via `output_config.format`** with the normalised JSON Schema; check
`stop_reason` for `"refusal"` and `"max_tokens"` before reading content.

**(d) `max_tokens` must cover thinking.** Adaptive thinking is on by default on Claude 5-family
models and `max_tokens` caps thinking **plus** text. The callers' `800` / `200` will truncate.
Either pass `thinking={"type": "disabled"}` with `output_config={"effort": "low"}`, or raise
`max_tokens` to ~4000. Note `disabled` is rejected on Opus 5 above `effort: "high"`.

(b) and (d) are easy to get wrong and never notice on the *fallback* path, which runs rarely.
Cover both in tests (§10).

### 6.3 Batch inference

S3 JSONL in, S3 out, roughly **half** the on-demand token price, drawing on a **separate quota
pool**. Used for: the §15 embedding backfill, nightly re-embedding of new listings, and offline
evaluation runs.

Orchestrate: EventBridge → Lambda (build manifest → S3) → `CreateModelInvocationJob` → completion
event → Lambda (results → vector store).

### 6.4 Guardrails

Bedrock Guardrails' **`ApplyGuardrail`** API evaluates text standalone, independent of
`InvokeModel` — so one managed policy (PII redaction, denied topics, prompt-attack detection) can
screen **both** the Qwen and Bedrock paths (verify current support for third-party model text).

For a consumer-facing real-estate consultant handling budget and personal circumstances, PII
redaction and fair-housing-adjacent denied topics deserve attention before launch.

### 6.5 Bedrock feature notes

| Feature | Bedrock | Relevance |
|---|---|---|
| Structured outputs | ✅ | §6.2(c) |
| Prompt caching (explicit `cache_control`) | ✅ | §16 |
| Automatic (top-level) prompt caching | ❌ | breakpoints are manual |
| Batch inference | ✅ | §6.3 |
| Server-side refusal `fallbacks` | ❌ | ours is client-side anyway (§3.3) |
| Files API, Managed Agents, web tools | ❌ | not used |

## 7. Configuration and IAM

```python
# --- AWS ------------------------------------------------------------------
aws_region: str = ""                       # required; clients apply no default
aws_access_key_id: str = ""                # omit when using an instance/task role
aws_secret_access_key: str = ""
aws_session_token: str = ""

# --- Qwen 0.5B on Lambda ---------------------------------------------------
qwen_function_name: str = ""               # e.g. "qwen-inference-prod"
qwen_model_version: str = "qwen-ft-2026-01"   # telemetry; bump per retrain
qwen_timeout_s: float = 30.0

# --- Bedrock ---------------------------------------------------------------
bedrock_chat_model: str = "anthropic.claude-sonnet-5"     # Messages API: `anthropic.` prefix
bedrock_effort: str = "low"
bedrock_disable_thinking: bool = True
bedrock_embedding_model: str = "cohere.embed-english-v3"  # bedrock-runtime: versioned IDs
bedrock_embedding_batch_size: int = 96
bedrock_guardrail_id: str = ""
bedrock_guardrail_version: str = ""

# --- Routing (§3) ----------------------------------------------------------
llm_route_intake_parse:     str = "qwen"
llm_route_opening_question: str = "bedrock"
llm_route_fit_explanation:  str = "bedrock"
llm_route_outreach_draft:   str = "bedrock"
llm_route_default:          str = "bedrock"
llm_route_fallback:         str = "bedrock"

# Cost telemetry. Qwen is GB-seconds, not tokens — see §19.
bedrock_input_cost_per_1m:  float = 0.0
bedrock_output_cost_per_1m: float = 0.0
qwen_cost_per_gb_second:    float = 0.0
```

Follow the existing `AliasChoices` pattern for conventional env names (`AWS_REGION`,
`AWS_ACCESS_KEY_ID`, …) so boto3's own resolution and our settings share one source of truth.

| Environment | Credentials |
|---|---|
| Local dev | `~/.aws/credentials` profile or `.env`; the default boto3 chain resolves both |
| Vercel | No IAM role — a dedicated IAM **user** key pair in project env vars |
| AWS compute (Part II) | IAM **role**. Static keys disappear |

Least-privilege policy, resources enumerated — the guardrail that stops a config typo from
invoking an unintended, far more expensive model:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:<region>:<acct>:function:qwen-inference-prod" },
    { "Effect": "Allow", "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:<region>::foundation-model/anthropic.claude-sonnet-5",
        "arn:aws:bedrock:<region>::foundation-model/cohere.embed-english-v3"
      ] },
    { "Effect": "Allow", "Action": ["bedrock:ApplyGuardrail"],
      "Resource": "arn:aws:bedrock:<region>:<acct>:guardrail/<guardrail-id>" }
  ]
}
```

### Dependencies

```
anthropic[bedrock]>=0.40.0
boto3>=1.35.0
```

Add to **both** `pyproject.toml` and `requirements.txt` — the Vercel runtime installs from
`requirements.txt` and they are hand-synced. Note `llama-cpp-python` lives in the **Lambda
container image**, not in the backend's dependencies — the backend only calls `lambda:Invoke`.

⚠️ **Cold-start budget.** `boto3` + `botocore` add ~15–20 MB and non-trivial import cost to a
Vercel bundle already carrying `openai`, `supabase`, `sqlalchemy`, `asyncpg`. Measure; if it
hurts, import `boto3` lazily inside the provider constructors and build singletons on first use
(`openrouter.py:176` sets the current pattern).

## 8. Error mapping

| Condition | Raiser | HTTP |
|---|---|---|
| Function name/region unset, credentials unresolvable | `raise_qwen_not_configured` | 503 |
| Lambda `TooManyRequestsException`, `ServiceException` | `raise_qwen_unavailable` | 503 → **fallback** |
| Invoke timeout, function timeout | `raise_qwen_request_timeout` | 504 → **fallback** |
| Handler returned `FunctionError` | `raise_qwen_invocation_failed` | 502 → **fallback** |
| `ValidationError` on the reply after one retry | `raise_qwen_completion_parse_failed` | 502 — **no fallback** (§3.3) |
| Bedrock throttle / access denied / timeout / refusal / parse | `raise_bedrock_*` | 503/504/502 |

Catch most-specific first. Keep user-facing copy identical across providers — these strings reach
the UI and must not vary by which backend served the request.

## 9. Telemetry

Keep the `llm_call` record compatible with `openrouter.py:89-101` so SolarWinds ingestion and
existing dashboards survive, and add what the hybrid needs:

```
provider="qwen"|"bedrock", model=<function name or bedrock id>,
task="intake_parse", outcome=..., duration_ms=...,
prompt_tokens=..., completion_tokens=..., total_tokens=...,
estimated_cost_usd=...,          # tokens for Bedrock; GB-seconds for Qwen
fallback_used=false, model_version="qwen-ft-2026-01",
billed_duration_ms=..., cold_start=false      # Qwen only, from the Lambda report
```

`task` and `model_version` are what let you answer "did the retrain regress intake parsing?"
without a deploy. `cold_start` tells you whether the warming ping (§5.4) is working.

## 10. Testing

Every provider takes an injectable client, so no network access is required.

| Test | Asserts |
|---|---|
| `test_routing::test_task_routes_to_configured_provider` | each `LlmTask` → the right provider |
| `test_routing::test_infra_error_triggers_fallback` | timeout/5xx → fallback called once |
| `test_routing::test_validation_error_does_not_fallback` | parse failure → raises, no second call |
| `test_routing::test_circuit_breaker_opens` | repeated failures stop hitting the primary |
| `test_qwen_lambda::test_payload_shape` | `schema_name` + messages reach the invoke payload |
| `test_qwen_lambda::test_temperature_forwarded` | Qwen **does** get `temperature` |
| `test_qwen_lambda::test_retry_on_invalid_json` | one retry, then raise |
| `test_bedrock_chat::test_system_message_extracted` | leading `system` turn → `system` param |
| `test_bedrock_chat::test_temperature_not_forwarded` | Claude **never** gets `temperature` |
| `test_bedrock_chat::test_thinking_disabled_and_max_tokens` | §6.2(d) — the easy-to-miss one |
| `test_bedrock_embeddings::test_batches_and_preserves_order` | 200 texts → chunked, input order |
| `test_schema_normaliser` | each output model → legal JSON Schema **and** valid GBNF grammar |

Plus a **grammar conformance test in the image build**: generate N outputs from the real model
under the grammar and assert every one validates against the Pydantic model. This is the check
that catches a schema change silently breaking §5.3.

And a **manual smoke check** in the deploy runbook (not CI): one intake parse (Qwen), one
similar-listings request (Bedrock), one forced fallback — confirming `provider`, `task`, and
`fallback_used` in the logs.

---

# Part II — Platform at scale

## 11. What changes and why

| Limitation today | Consequence under load |
|---|---|
| `find_similar_listings` embeds up to **101 texts per request** | Per-request cost scales with pool size; re-embeds the same listings forever |
| Vercel timeout, no queue | A slow call becomes a user-visible 5xx |
| Postgres connection per concurrent request | Exhaustion before anything else breaks |
| No response or prompt cache | Every identical prompt pays full price |

**§15 is the highest-impact item** and does not depend on any of the rest.

Note what is *not* in this list any more: model capacity. A 0.5B on Lambda scales horizontally by
default, and Bedrock quotas only bind the three lower-volume paths. The scale problems here are
ordinary web-application problems.

## 12. Capacity and the cost crossover

With a CPU model on Lambda, the ceiling is **account concurrency** (default ~1,000 per region,
raisable), not GPU capacity.

```
peak_requests_per_sec × seconds_per_request  =  concurrent executions needed
```

At ~2 s per intake parse, the default 1,000 concurrency serves **~500 requests/sec** — far beyond
any plausible near-term traffic. Request a limit increase when approaching it; that is the whole
capacity plan.

**Cost crossover.** Lambda is cheapest when traffic is spiky or low, because idle is free. Fargate
is cheaper per unit of sustained CPU (roughly 2–3× cheaper per vCPU-hour). So:

| Volume | Cheapest home for the model |
|---|---|
| MVP (< ~65k calls/month) | **Lambda — free tier covers it** |
| Growing (spiky, unpredictable) | **Lambda — pay only for what runs** |
| High sustained | **In-process on the Fargate tasks you already run** (§5.6) — $0 marginal |

The pleasant consequence of a 0.5B model: every option on that list is cheap, and the migration
between them is a config change plus a container rebuild. There is no capacity commitment to buy
and no wrong answer that costs thousands to unwind.

## 13. Compute — the API tier

This section is about the **API tier**, not the model (which is §5).

| | Lambda | Fargate (ECS) |
|---|---|---|
| Scale-out | Near-instant | Minutes |
| Idle-while-waiting cost | **Pays GB-s for the whole blocked call** | Free — async event loop absorbs it |
| Concurrency per unit | 1 request per environment | Hundreds per task (async FastAPI, I/O-bound) |
| DB connections | **One per concurrent execution** → exhaustion (§17) | Pooled per task |
| Fit for existing code | Needs an adapter (Mangum) | **Runs `app.main:app` unchanged** |

**Recommendation: Fargate for the API tier.** The backend is already async FastAPI, and its calls
to Qwen-Lambda or Bedrock are I/O-bound waiting — one async task handles hundreds concurrently at
no extra cost, while API-tier Lambda would bill wall-clock for every blocked second *and* hold a
database connection throughout.

The distinction from §5 is the point: **Lambda for the model** (CPU work you should pay for),
**Fargate for the API** (network waiting you should not).

And once on Fargate, §5.6's endgame becomes available — fold the 0.5B into the API container and
delete the separate function entirely.

### 13.1 Where AWS Lambda fits — the inventory

| Function | Trigger | Job | Phase |
|---|---|---|---|
| **`qwen-inference`** | `lambda:Invoke` from the API | **Run the 0.5B, return grammar-constrained JSON** | **C** |
| `qwen-warmer` | EventBridge, every 5 min | Ping `qwen-inference` to keep one environment warm (§5.4) | C |
| `listing-ingest` | S3 `ObjectCreated` on `raw-listings/` | Normalise feed → upsert Postgres row → enqueue embed job | B |
| `embed-worker` | SQS | Call Bedrock Cohere v3 → write vector to the store | B |
| `batch-manifest-builder` | EventBridge (nightly) | Pending listings → JSONL → S3 → `CreateModelInvocationJob` | B |
| `batch-result-loader` | EventBridge (Bedrock job completion) | Read S3 results → write vectors | B |
| `deferred-llm-worker` | SQS | Fit explanation / outreach draft → Bedrock | F |

Two constraints:

- **Cap event-source concurrency** on SQS-driven workers so Lambda's willingness to scale cannot
  outrun the Bedrock quota.
- **Idempotency keys in DynamoDB.** SQS redelivery is normal; without a dedupe check a retry burns
  a second Bedrock call for a result you already have.

## 14. Queue and backpressure

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  EDGE                                                                        ║
║    Route 53 (latency routing)  ──▶  CloudFront  ──▶  AWS WAF + Shield        ║
╚═══════════════════════════════════════╤══════════════════════════════════════╝
                                        ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║  APPLICATION                                                                 ║
║    ALB  ──▶  ECS Fargate :  FastAPI `app.main:app`   (2–6 tasks, autoscaled) ║
║                             └── providers/routing.py  (per-task + fallback)  ║
╚═══╤════════════════╤═══════════════════╤═══════════════════╤═════════════════╝
    │                │                   │                   │
    ▼                ▼                   ▼                   ▼
┌───────────────┐┌──────────────────┐┌──────────────┐┌──────────────────────────┐
│ MODEL         ││ ASYNC / EVENT    ││ CACHE        ││ DATA                     │
│               ││                  ││              ││                          │
│ Lambda        ││ SQS ──▶ Lambda   ││ ElastiCache  ││ Postgres (Supabase)      │
│  qwen-        ││  ├ deferred-llm  ││  • response  ││   via RDS Proxy /        │
│  inference    ││  ├ embed-worker  ││    cache     ││   pgbouncer              │
│  (0.5B, CPU)  ││  ├ listing-      ││  • rate      ││ DynamoDB                 │
│               ││  │   ingest      ││    limiter   ││   session · idempotency  │
│ Bedrock       ││  ├ batch-*       ││  • circuit   ││ Vector store             │
│  • cohere-v3  ││  └ qwen-warmer   ││    breaker   ││   pgvector → OpenSearch  │
│  • claude-5   ││                  ││              ││ S3                       │
│  • Guardrails ││ EventBridge      ││              ││   feeds · batch I/O ·    │
│  • batch      ││ DLQ + alarms     ││              ││   uploads                │
└───────────────┘└──────────────────┘└──────────────┘└──────────────────────────┘
        │                 │                  │                    │
        └─────────────────┴────────┬─────────┴────────────────────┘
                                   ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║  OBSERVABILITY                                                               ║
║    CloudWatch + EMF  ·  X-Ray  ·  Firehose ─▶ S3 ─▶ Athena  ·  SolarWinds    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

| Class | Path | Under pressure |
|---|---|---|
| **Interactive** — intake parse, opening question | Sync → Qwen Lambda / Bedrock | Bounded retry; then fallback (§3.3); then degrade |
| **Deferred** — fit explanation, outreach draft, embedding backfill | SQS → Lambda → Bedrock | Queued. No user impact |

**Interactive path:**

```
┌─────────┐
│ Browser │  POST /intake_sessions/{id}/answers/llm
└────┬────┘
     ▼
┌──────────────────────────────────────────────────────────────────┐
│ CloudFront ─▶ WAF ─▶ ALB ─▶ Fargate (FastAPI)                    │
└────┬─────────────────────────────────────────────────────────────┘
     │ ① routing.resolve_chat_provider(task=INTAKE_PARSE)
     │ ② ElastiCache response-cache lookup ────── hit ─────────────▶ return
     │ ③ miss
     ▼
┌────────────────────────────────┐   ④ infra   ┌────────────────────────────┐
│ Lambda: qwen-inference         │   failure   │ Bedrock                    │
│ Qwen 0.5B, CPU, GBNF grammar   │ ──────────▶ │ anthropic.claude-sonnet-5  │
└────┬───────────────────────────┘  timeout /  └─────────────┬──────────────┘
     │ ok                            throttle /              │ ok
     │                               breaker                 │
     └───────────────┬──────────────────────────────────────┘
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ validate JSON ─▶ persist criteria (Postgres) ─▶ cache ─▶ respond │
└──────────────────────────────────────────────────────────────────┘

  ④ fires on infrastructure failure ONLY — never on a validation error,
    which would just buy the same bad answer twice (§3.3).
```

**Deferred path:**

```
┌─────────┐  POST (fit explanation / outreach draft)
│ Browser │───────────────┐
└────▲────┘               ▼
     │            ┌────────────────┐  enqueue   ┌───────────┐
     │            │ Fargate        │───────────▶│    SQS    │
     │            │ (FastAPI)      │ 202 + jobId└─────┬─────┘
     │            └────────────────┘                  ▼
     │                                    ┌───────────────────────┐
     │                                    │ Lambda                │
     │                                    │ deferred-llm-worker   │
     │                                    └───────────┬───────────┘
     │                                                │ Bedrock InvokeModel
     │                                                ▼
     │                                    ┌───────────────────────┐
     │                                    │ result ─▶ Postgres    │
     │   WebSocket / SSE push             └───────────┬───────────┘
     └────────────────────────────────────────────────┘

                  poison messages ─────▶ DLQ (CloudWatch alarm)
```

Deciding which call sites are genuinely interactive is a product question worth answering early —
every path moved to the deferred class buys interactive headroom.

Mechanics: visibility timeout > worst-case latency; `maxReceiveCount` → DLQ + alarm; capped
event-source concurrency; idempotency keys in DynamoDB. For results the client waits on, use
WebSocket API or SSE rather than polling.

## 15. Vector search — the biggest single win

**Today:** every similar-listings request embeds the seed plus up to 100 candidates
(`similar_listings.py:52-55`), then computes cosine similarity in Python
(`app/domain/similarity.py`). The same listings are re-embedded on every request, forever.

**Target:** embed each listing **once at ingest**; at query time embed only the seed.

```
INGEST  (off the request path — runs once per listing, ever)

┌────────────────┐  ObjectCreated  ┌────────────────────┐
│ S3             │────────────────▶│ Lambda             │
│ raw-listings/  │                 │ listing-ingest     │
└────────────────┘                 └─────────┬──────────┘
                                             │ normalise, upsert
                                             ▼
                                   ┌────────────────────┐
                                   │ Postgres           │
                                   │ listing row        │
                                   └─────────┬──────────┘
                                             │ enqueue embed job
                                             ▼
                                   ┌────────────────────┐
                                   │ SQS                │
                                   └─────────┬──────────┘
                                             ▼
                                   ┌────────────────────┐  InvokeModel  ┌──────────┐
                                   │ Lambda             │──────────────▶│ Bedrock  │
                                   │ embed-worker       │◀──────────────│ cohere-v3│
                                   └─────────┬──────────┘  1024-dim vec └──────────┘
                                             ▼
                                   ┌──────────────────────────────────┐
                                   │ VECTOR STORE                     │
                                   │ pgvector (now) → OpenSearch      │
                                   └──────────────────────────────────┘

  Backfill / nightly:
    EventBridge ─▶ Lambda batch-manifest-builder ─▶ S3 JSONL
                     ─▶ Bedrock BATCH job ─▶ S3 results
                          ─▶ Lambda batch-result-loader ─▶ vector store


QUERY  (request path — one embedding call, regardless of corpus size)

┌────────────┐   ┌────────────────┐   ┌──────────────────────────────────────┐
│ seed       │──▶│ 1 embed call   │──▶│ k-NN search                          │
│ listing    │   │ (Bedrock)      │   │ pre-filter: state, city, prop_type   │
└────────────┘   └────────────────┘   │ ──▶ top-k with scores  (single-ms)   │
                                      └──────────────────────────────────────┘
```

| | Today | With ingest-time embeddings |
|---|---|---|
| Embedding calls per request | up to **101** | **1** |
| Similarity | Python, over a 40–100 row pool | ANN index, over the whole corpus |
| Quality | capped by the pre-filtered pool | true nearest neighbours corpus-wide |

The quality gain isn't incidental: `DEFAULT_CANDIDATE_POOL = 40` means the true nearest neighbour
may never enter the ranking at all.

**Where to put the vectors:** start with **pgvector** in the existing Postgres — the win is
*ingest-time embedding*, not the index technology, and OpenSearch Serverless carries a minimum OCU
floor that is poor value at low traffic. Move to OpenSearch when listing count outgrows HNSW
maintenance on the primary, hybrid keyword+vector search becomes a requirement, or Bedrock
Knowledge Bases is adopted.

Either way the application change is identical: a `VectorIndex` protocol beside the existing
provider protocols, with `pgvector` and `opensearch` implementations.

**Migration:** a backfill embedding the existing corpus — run it through Bedrock batch inference
(§6.3). Dimension is fixed by the model (1024 for Cohere v3); changing it later means a full
re-index, so treat that choice as durable.

## 16. Caching

| Layer | Caches | Effect |
|---|---|---|
| **ElastiCache (Valkey) response cache** | hash(system + user + model + params) → response | Removes the call entirely — Lambda GB-seconds or Bedrock tokens |
| **Bedrock prompt caching** (`cache_control`) | stable system prefixes on the Bedrock paths | Up to ~90% off cached input tokens |
| **CloudFront** | static frontend, cacheable GETs | Removes origin load |

Response caching applies best to the **opening-question** path (deterministic given a question
row) — which is why that path's Bedrock cost stays low despite using a frontier model. Intake
parse is user-specific and will rarely hit.

For Bedrock prompt caching, place the `cache_control` breakpoint at the end of the stable prefix
and verify with `cache_read_input_tokens` in the `llm_call` log — automatic top-level caching is
not available on Bedrock, and any per-request value interpolated into the prefix silently
invalidates everything after it.

## 17. Data layer and the connection-pool trap

The existing config already shows awareness — `db_serverless` enables NullPool and disables
prepared statements for pgbouncer transaction mode (`config.py:22-27`).

> **Serverless compute + Postgres = connection exhaustion.** Each concurrent Lambda execution
> holds a connection.

Note this applies to the **API tier**, not to `qwen-inference`, which touches no database — one
more reason the model-on-Lambda / API-on-Fargate split is clean.

In order: **Fargate for the API tier** (§13); **RDS Proxy** or pgbouncer if Lambda ever does
request-path database access; **DynamoDB for hot-path state** — session state, idempotency keys,
rate-limit counters.

**Keep Supabase Postgres as the system of record** unless there's a concrete reason not to.

### 17.1 S3 and ECR — where artifacts live

Model weights ship **inside the Lambda container image**, which lives in **ECR**, not S3 (§5.2).
That is a deliberate simplification: no runtime download, no EFS mount, and the image digest *is*
the version. S3's remaining roles are data-plane and telemetry.

```
        ┌──────────────────────────┐        ┌──────────────────────────────────┐
        │           ECR            │        │                S3                │
        └──────────────────────────┘        └──────────────────────────────────┘

  qwen-inference:<tag>                  ── DATA PLANE ──────  ── TELEMETRY ─────────
    └─ weights + llama.cpp +               raw-listings/         model-invocation-logs/
       pre-compiled GBNF grammars            └─▶ S3 event         └─ Bedrock full
    └─▶ Lambda pulls at deploy                  ─▶ Lambda            request+response
                                                  listing-ingest
  ROLLBACK = redeploy the                                          analytics/
  previous image tag                     batch-inference/            └─ Firehose ─▶ Athena
                                           ├ input/  ◀── manifest
                                           └ output/ ──▶ results     eval/golden-sets/
                                                                       └─ regression gate
                                         vector-snapshots/                before promotion
                                           └─▶ per-region rebuild

                                         user-uploads/
                                           └─▶ CloudFront (OAC + signed URLs)
```

| Store | Contents | Why |
|---|---|---|
| **ECR** | `qwen-inference` images — weights, runtime, grammars | Immutable, digest-versioned. **Rollback = redeploy the previous tag** |
| S3 `raw-listings/` | Ingestion feed | Entry point; S3 event triggers `listing-ingest` |
| S3 `batch-inference/{input,output}/` | JSONL manifests + results | **Transport** for Bedrock batch (§6.3) |
| S3 `vector-snapshots/` | Embedding snapshots | Vectors are derived data — rebuild per region, don't replicate |
| S3 `user-uploads/` | Avatars, documents | Currently Supabase Storage; migrate at scale |
| S3 `model-invocation-logs/`, `analytics/` | Bedrock capture, Firehose telemetry | Eval, audit, cost analytics |
| S3 `eval/golden-sets/` | Fixed intake prompts + expected criteria | **Regression gate before promoting a retrain** — see §21.4 |

**Layout:** separate buckets by security and lifecycle boundary, not one bucket with prefixes.

**Cost:** add a **VPC Gateway Endpoint for S3** — it is free, and without it every byte between
your VPC and S3 is billed per-GB through NAT Gateway (§19). Same for DynamoDB; interface
endpoints for Bedrock and Lambda.

⚠️ **Privacy.** `model-invocation-logs/` records **full prompts and completions** — for this
product that means budget, location, financial circumstances, and free-text personal detail from
intake. Enabling capture "for debugging" and forgetting creates a durable PII store nobody scoped.
If you enable it: sample rather than capture everything, set an explicit lifecycle expiry, encrypt
with SSE-KMS under a dedicated key, restrict read access separately, and consider running
Guardrails PII redaction (§6.4) *before* the capture write. Add a bucket policy denying non-TLS
requests across all buckets.

**Lifecycle:** raw feeds → Glacier after ~30 days; telemetry → Glacier then expire on the
retention commitment; batch input/output → expire after a few days (transport, not records); ECR
→ lifecycle policy keeping the last N image tags, never the one currently deployed.

## 18. Multi-region, observability, guardrails

**Multi-region** is now cheap on the model side — a 0.5B Lambda deploys to a second region for
near-nothing, and Bedrock has independent per-region quotas. The cost is in the data tier, not the
model tier. Justify it with an availability SLO. If adopted: Route 53 latency routing; decide
Postgres write locality explicitly; rebuild vector indexes per region from S3.

**Observability:** CloudWatch + EMF; X-Ray across ALB → Fargate → Lambda / Bedrock; Lambda metrics
(duration, `billed_duration`, concurrent executions, cold-start rate, errors, throttles); Bedrock
model-invocation logging → S3; Firehose → S3 → Athena. Keep the SolarWinds shipping and the
`llm_call` shape (§9).

Alarms that matter: **`fallback_used` rate** (§3.3), Qwen p99 duration and cold-start rate, Lambda
throttles, SQS depth and message age, DLQ depth, DB connection utilisation, cache hit rate, cost
anomaly.

**Abuse control:** Guardrails via `ApplyGuardrail` across both providers (§6.4); WAF rate limiting,
bot control, Shield; **per-tenant budgets** at our own limiter. That last one is pure application
logic; nothing in AWS does it for you.

## 19. Cost shape

The headline: **there is no expensive component in this design.** The GPU line item that dominated
earlier drafts is gone.

| Component | Shape |
|---|---|
| **Lambda `qwen-inference`** | Per GB-second + per request. **Free tier likely covers MVP entirely** (§5.6); ~$0.0001/call beyond it |
| ECR image storage | ~$0.10/GB/month. Cents |
| CloudWatch Logs | Per GB ingested. Set retention; do not log full prompts by default |
| Bedrock (embeddings, general chat, guardrails) | Per token. The largest LLM line item, and it is small |
| Bedrock batch inference | ~50% of on-demand; separate quota |
| Fargate (API tier) | Per vCPU/GB-second, continuous, predictable |
| ElastiCache | Per node-hour, continuous — the first component with a real monthly floor |
| OpenSearch Serverless | **Minimum OCU floor regardless of traffic** — why §15 starts on pgvector |
| NAT Gateway | Per hour **and per GB** — the S3 gateway endpoint is free; not having it is a pure loss |

Largest savings levers, in order: **ingest-time embeddings** (§15), **response caching on the
opening-question path** (§16), **Lambda memory tuning** (§5.4 — the setting that minimises
cost is often not the smallest one), and **routing the three general paths to Haiku** if Sonnet
proves more than they warrant.

## 20. Rollout

| Phase | Work | Why here |
|---|---|---|
| **A — Routing layer** | `routing.py`, `LlmTask`, `task=` on four call sites, fallback + circuit breaker. All routes still OpenRouter/HF | Pure refactor, no behaviour change, no AWS. Unblocks everything |
| **B — Ingest-time embeddings** | `VectorIndex` protocol, pgvector + HNSW, ingest path, backfill, rewrite `find_similar_listings` | Biggest cost/quality win. **Ships on Vercel + Supabase, no infra migration** |
| **C — Qwen on Lambda** | Container image, GBNF grammars, `qwen_lambda.py`, warmer, memory tuning; route `intake_parse` | The main event. Fallback from A means a bad deploy degrades rather than breaks |
| **D — Bedrock embeddings** | `bedrock_embeddings.py`; route embeddings to Cohere v3 | Small, isolated; 384 → 1024-dim quality upgrade |
| **E — Bedrock general chat + guardrails** | `bedrock_chat.py`, `ApplyGuardrail`, alarms | Moves the other three paths off OpenRouter |
| **F — Runtime to AWS** | VPC, ALB + Fargate running `app.main:app`, RDS Proxy/pgbouncer, CloudFront + WAF, IAM roles replace static keys | Removes the Vercel ceiling; enables §5.6's in-process endgame |
| **G — Scale** | SQS + deferred workers, caching, OpenSearch if triggered, multi-region if the SLO demands | Only after the above |

**A and B ship before any AWS work at all**, and are worth doing even if C never happens.

## 21. Open questions

1. **Quantisation and measured latency.** Which GGUF quant (Q4_K_M / Q8_0 / fp16), and what is the
   p50/p99 wall time on a representative intake prompt at 3,008 MB? Every number in §12 and §19
   follows from this and nothing else. Benchmark before phase C.
2. **Does the grammar path hold?** Constrained decoding is the make-or-break for a 0.5B doing
   structured extraction (§5.3). Prove it against the real schemas early — this is the single
   largest technical risk in the plan.
3. **Sonnet or Haiku for the three general paths?** A config decision, but it is the largest
   remaining LLM line item.
4. **Retrain cadence and promotion gate.** Versioned image tags and `model_version` telemetry (§9)
   only help if there's a defined process — a golden set in `eval/golden-sets/` and a pass
   threshold — for evaluating a new fine-tune before it takes production traffic.
5. **Cold start tolerance.** Is a few-second p99 on the first request after idle acceptable, or
   does the product need provisioned concurrency (and its continuous bill)?
6. **Which call sites are genuinely interactive?** Determines what moves behind SQS in phase G.
7. **Does Supabase stay?** Recommended yes; migrating is a separate project.
