# LLM Platform Architecture — Qwen on Lambda + Bedrock

Status: in progress (Part I steps 1–3 implemented on `feat/bedrock-llm-platform`)
Scope: `backend/**`, deployment and infrastructure
Author: engineering

> Revision history: an earlier draft assumed a ~7B model on an always-on GPU. The actual model is
> **Qwen 0.5B fine-tuned for one task**, which runs on CPU. A later revision assumed a full AWS
> runtime migration; this one **deliberately stays on Vercel and avoids every service with a
> standing monthly cost** (§21). Filename kept so existing links resolve.

---

## 0. The design in one table

| Workload | Runs on | Standing cost |
|---|---|---|
| **Criteria extraction** from free-text input (intake parse) | **Qwen 0.5B on AWS Lambda (CPU)** | **$0** — perpetual free tier |
| **Embeddings** | **Bedrock** `cohere.embed-english-v3` | **~cents/month** after §15 |
| **Vector search** | **pgvector in the existing Supabase Postgres** | **$0** |
| **General chat** — opening question, fit, outreach | **OpenRouter** (today's provider) | ~$0 |
| **Fallback** when Qwen fails | Bedrock, or OpenRouter | pay-per-use, rarely hit |
| **Bulk/backfill** embedding jobs | **Bedrock batch inference** (S3 in/out) | one-off, ~50% rate |
| **Guardrails** on input/output | **Bedrock `ApplyGuardrail`** | per text unit, opt-in |
| **API tier** | **Vercel** (unchanged) | current bill |

### Deliberately not using

Each of these has a standing monthly charge that buys nothing at current volume. They are not
rejected forever — §21 records what would justify each.

| Service | Why not | Would cost |
|---|---|---|
| **OpenSearch Serverless** | pgvector delivers the entire §15 win for $0 | **~$350–700/mo floor, regardless of traffic** |
| **Fargate + ALB** | Vercel already runs the API | ~$40/mo |
| **NAT Gateway** | No VPC ⇒ no NAT. Lambda runs outside a VPC and reaches AWS APIs over IAM-authenticated public endpoints | ~$32/mo + per-GB |
| **ElastiCache** | In-process and Postgres substitutes are adequate at this volume (§16) | ~$15/mo after the 12-month tier |
| **Bedrock chat (Sonnet 5)** | OpenRouter already serves these three paths | ~$30/mo |
| **SageMaker** | Lambda's free tier is perpetual; SageMaker's is a 2-month trial | few $/mo |

### The picture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          REAL ESTATE CONSULTANT                              │
│                                                                              │
│   ┌────────────┐            ┌──────────────────────────────────┐             │
│   │  Next.js   │───────────▶│   FastAPI backend  (Vercel)      │             │
│   │  (Vercel)  │            │      providers/routing.py        │             │
│   └────────────┘            └───┬──────────────┬───────────┬───┘             │
│                                 │              │           │                 │
│            ┌────────────────────┘              │           └──────────┐      │
│            ▼                                   ▼                      ▼      │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌──────────────────┐│
│  │   A W S   L A M B D A │   │     B E D R O C K     │   │    SUPABASE      ││
│  │ ┌───────────────────┐ │   │ ┌───────────────────┐ │   │ ┌──────────────┐ ││
│  │ │ qwen-inference    │ │   │ │ cohere.embed-v3   │ │   │ │ Postgres     │ ││
│  │ │ Qwen 0.5B, CPU    │ │   │ │ embeddings        │ │   │ │ + pgvector   │ ││
│  │ │ container (ECR)   │ │   │ ├───────────────────┤ │   │ │              │ ││
│  │ │ grammar JSON      │ │   │ │ Guardrails        │ │   │ │ listings +   │ ││
│  │ ├───────────────────┤ │   │ ├───────────────────┤ │   │ │ vectors      │ ││
│  │ │ listing-ingest    │ │   │ │ batch inference   │ │   │ └──────────────┘ ││
│  │ │ embed-worker      │ │   │ └───────────────────┘ │   │                  ││
│  │ └───────────────────┘ │   │                       │   │ existing bill    ││
│  │  free tier · no VPC   │   │  cents/month          │   └──────────────────┘│
│  └───────────────────────┘   └───────────────────────┘                       │
│                                                                              │
│         ┌──────────────────┐   general chat (opening question, fit,          │
│         │   OPENROUTER     │◀── outreach) stays here — already ~free         │
│         └──────────────────┘                                                 │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Two tiers

| Tier | What | When |
|---|---|---|
| **Part I** (§1–§10) | Routing + Bedrock providers + the Qwen Lambda, behind the existing protocol seam | Now |
| **Part II** (§11–§22) | Ingest-time embeddings, queueing, observability — all within the free tier | Next |

---

# Part I — Providers and routing

## 1. Goals

- Serve the fine-tuned Qwen 0.5B for criteria extraction, on CPU, inside the Lambda free tier.
- Use Bedrock where it is nearly free (embeddings) or uniquely useful (guardrails, batch).
- Route **per call site**, so cost is opted into per path rather than discovered on a bill.
- Keep OpenRouter/HF as the default for everything not explicitly moved.

Non-goals: streaming, agentic tool loops, replacing Supabase, any GPU, any standing monthly cost.

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

Two protocols, `ChatProvider` and `EmbeddingsProvider` (`providers/base.py`); nothing above the
seam touches a vendor SDK.

**One structural gap:** `resolve_chat_provider()` returns a *single* provider for all chat. Qwen
serves exactly one of four paths, so per-task routing is required. That is §3.

## 3. Model routing — the centerpiece

### 3.1 The routing table

The fine-tune covers **one** task. Everything else stays where it is.

| Call site | Code | Route | Standing cost |
|---|---|---|---|
| **Intake parse** | `llm/intake/service.py:62` | **Qwen 0.5B (Lambda)** | $0 |
| Opening question | `llm/intake/service.py:100` | OpenRouter | ~$0 |
| Fit explanation | `llm/fit/service.py` | OpenRouter | ~$0 |
| Outreach draft | `llm/outreach/service.py` | OpenRouter | ~$0 |
| Embeddings | `services/similar_listings.py:55` | **Bedrock Cohere v3** | cents |

A 0.5B fine-tuned on one task can beat a general 8B *at that task* while being ~16× smaller —
that is the point. It will not transfer to the other three, and asking it to is the fastest way
to conclude the fine-tune "doesn't work."

**Bedrock chat is built but not routed.** `BedrockChatProvider` exists (§6.2) and can take any of
the three general paths by changing one env var — worth roughly $30/month if the quality proves
worth it. Until then it costs nothing to have.

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

One env var per task — routing changes are a redeploy, never a code change. **Defaults keep every
paid path off:**

```python
llm_route_intake_parse:     str = "openrouter"   # → "qwen" once that branch merges
llm_route_opening_question: str = "openrouter"
llm_route_fit_explanation:  str = "openrouter"
llm_route_outreach_draft:   str = "openrouter"
llm_route_embeddings:       str = "huggingface"  # → "bedrock" in phase D
llm_route_default:          str = "openrouter"
llm_route_fallback:         str = "openrouter"
```

Call sites gain one keyword argument:

```python
parsed_output = await generate_structured_output(
    messages=[...], response_format=LlmParseModelOutput,
    temperature=0.1, max_tokens=800,
    task=LlmTask.INTAKE_PARSE,          # ← new
)
```

Four one-line edits. `task` defaults to `None` → `llm_route_default`, so an un-annotated call site
still works.

### 3.3 Fallback — explicit, bounded, logged

Fallback matters here because the primary is a self-hosted model with no vendor SLA, and a 0.5B
has less headroom on unusual input than a large model.

- Trigger on **infrastructure failure only** — Lambda invoke error, timeout, throttle, breaker
  open. **Never** on a validation failure or refusal; that just buys the same bad answer twice.
- One attempt, no chaining.
- Log `fallback_used=true` with the reason and alarm on the rate. A silent fallback running for a
  week is how you discover the Qwen function has been broken since Tuesday.
- **Circuit breaker in-process** (per Vercel instance) rather than ElastiCache — see §16. Less
  precise than a shared breaker, adequate at this volume, and free.

## 4. Target architecture

```
┌─────────────────────── FastAPI backend (Vercel) ─────────────────────────────┐
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
│         │  • in-process circuit breaker    │                  │              │
│         └────────────────┬─────────────────┘                  │              │
└──────────────────────────┼────────────────────────────────────┼──────────────┘
     ┌──────────┬──────────┴────────┬─────────────┐             │
     ▼          ▼                   ▼             ▼             ▼
┌───────────┐┌────────────┐  ┌────────────┐┌───────────┐ ┌──────────────────┐
│ QwenLambda││ BedrockChat│  │ OpenRouter ││HuggingFace│ │ BedrockEmbeddings│
│ Provider  ││ Provider   │  │  Provider  ││ Provider  │ │ Provider         │
├───────────┤├────────────┤  ├────────────┤├───────────┤ ├──────────────────┤
│ boto3     ││ anthropic  │  │ openai SDK ││openai SDK │ │ boto3            │
│ lambda    ││ SDK Mantle │  │            ││           │ │ bedrock-runtime  │
├───────────┤├────────────┤  ├────────────┤├───────────┤ ├──────────────────┤
│ Qwen 0.5B ││ claude-    │  │ llama-3.1- ││ MiniLM    │ │ cohere.embed-    │
│ CPU, GGUF ││ sonnet-5   │  │ 8b         ││ 384-dim   │ │ english-v3       │
└───────────┘└────────────┘  └────────────┘└───────────┘ └──────────────────┘
 INTAKE PARSE  built, not      3 GENERAL     current       EMBEDDINGS
   (phase E)    routed          PATHS        embeddings     (phase D)
```

### New/changed files

| File | Status |
|---|---|
| `app/core/config.py` — AWS + Bedrock settings | ✅ step 1 |
| `app/llm/providers/exceptions.py` — `raise_bedrock_*` | ✅ step 2 |
| `app/llm/providers/bedrock_chat.py` — `BedrockChatProvider` | ✅ step 3 |
| `app/llm/providers/bedrock_embeddings.py` — `BedrockEmbeddingsProvider` | step 4 |
| `app/llm/providers/{chat,embeddings}.py` — add `"bedrock"` | step 5 |
| `app/llm/providers/routing.py` — `LlmTask`, fallback, breaker | step 6 |
| `app/llm/{intake,fit,outreach}/service.py` — `task=` kwarg | step 7 |
| `app/repositories/properties.py` — vector upsert + k-NN query | phase B |
| `infra/qwen-lambda/` — Dockerfile, handler, model, grammars | phase E |

## 5. Hosting Qwen 0.5B on Lambda

### 5.1 Why CPU, and why Lambda

Qwen 0.5B is ~1 GB at bf16, ~500 MB at int8, ~350 MB at 4-bit, and criteria extraction emits only
~100–200 output tokens. That is a **CPU workload measured in seconds**. Once the GPU is gone the
requirement is: run occasionally, cost nothing when idle, need no cluster. That is Lambda, and its
free tier is **perpetual** — 1M requests and 400,000 GB-seconds every month, indefinitely.

At ~3 GB × ~2 s = 6 GB-s per call, that is roughly **65,000 free calls per month**.

**No VPC.** The function needs no private network access — it reaches nothing but the caller.
Keeping it outside a VPC avoids NAT Gateway entirely, which is the single largest avoidable cost
in an AWS deployment of this shape.

### 5.2 Container image and runtime

Lambda container images support up to 10 GB, so the weights ship **inside the image** — no
cold-start download, no EFS mount.

```
infra/qwen-lambda/
├── Dockerfile          # FROM public.ecr.aws/lambda/python:3.12
├── handler.py          # load once at module scope, reuse across warm invocations
├── model/
│   └── qwen-0.5b-ft.Q8_0.gguf
└── schemas/            # pre-compiled GBNF grammars per output schema
```

**Runtime: `llama.cpp` (via `llama-cpp-python`) with a GGUF quant** — smallest image, `mmap`
weight loading, and native GBNF grammar support, which §5.3 depends on.

### 5.3 Constrained JSON output — non-negotiable

Small models are markedly worse at reliably emitting valid JSON. This is the biggest technical
risk in the plan, and it has a clean solution: **constrain the decoder** so invalid output is
impossible rather than unlikely.

```
Pydantic model  ──▶  JSON Schema  ──▶  GBNF grammar  ──▶  llama.cpp sampler
```

- Generate the grammar at **build time** and bake it into the image; the schema only changes when
  you deploy.
- Still call `model_validate_json`. The grammar guarantees *shape*, not *sense*.
- On `ValidationError`: one retry, then fall back (§3.3).

Do not ship this relying on prompt instructions alone. It will pass testing and fail in production
on the inputs that matter.

### 5.4 Memory, CPU, and cold starts

Lambda allocates CPU in proportion to memory — ~1 vCPU at 1,769 MB, ~2 at 3,008 MB. More memory
means shorter duration, which can make a larger setting **cheaper overall**. Run Lambda Power
Tuning across 1,769 / 3,008 / 5,120 MB with a real intake prompt and pick from the measured curve.
Start at 3,008 MB.

**Cold start** is container init plus model load — a few seconds with `mmap`. Mitigation:
**EventBridge ping every 5 minutes** keeps one environment warm (~8,600 invocations/month, inside
the free tier). Provisioned concurrency bills continuously and defeats the reason we chose Lambda;
only if p99 becomes a stated requirement.

Also set timeout ~30 s and **reserved concurrency** as a cost blast-radius cap.

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

- **`temperature` works here**, unlike the Bedrock path (§6.2) which rejects it. That asymmetry is
  precisely why routing is per-task.
- boto3 is synchronous → `anyio.to_thread.run_sync` (via Starlette, no new dependency).
- Invoke over IAM rather than a Function URL — no public endpoint to secure.
- Reuse `split_system_prompt` from `bedrock_chat.py`.

## 6. Bedrock — the parts worth paying for

### 6.1 Embeddings — `cohere.embed-english-v3`

`bedrock-runtime` `InvokeModel`, versioned model IDs.

| Candidate | Dims | Batch/call | Fit |
|---|---|---|---|
| **`cohere.embed-english-v3`** | 1024 | ~96 | ✅ recommended |
| `cohere.embed-multilingual-v3` | 1024 | ~96 | ✅ if non-English listings appear |
| `amazon.titan-embed-text-v2:0` | 1024 | **1** | ⚠️ needs fan-out |

Cost after §15 is roughly **$0.00002 per search** — the cheapest meaningful upgrade available
(384-dim MiniLM → 1024-dim Cohere v3).

Implementation: chunk to `bedrock_embedding_batch_size` (96); **preserve order** —
`similar_listings.py:61` zips vectors positionally against candidate rows, so reordering silently
mis-scores every listing; assert `len(vectors) == len(texts)`.

### 6.2 Chat — built, not routed

`BedrockChatProvider` (implemented, step 3) via `AsyncAnthropicBedrockMantle`. Model IDs carry an
`anthropic.` prefix and no date suffix. Four adaptations, all inside the provider:

**(a) `system` is a top-level parameter**, not a message — `split_system_prompt` handles it.

**(b) `temperature` is dropped.** Claude 4.7+ rejects it; Sonnet 5 rejects non-default values.

**(c) Structured output via `messages.parse(output_format=...)`** — the SDK generates the schema
and validates client-side, so no hand-written normaliser is needed.

**(d) Thinking off** (`bedrock_disable_thinking`). Adaptive thinking counts against `max_tokens`,
and callers size it at 800/200 for models without thinking.

### 6.3 Batch inference

S3 JSONL in, S3 out, ~half the on-demand rate, separate quota pool. Used for the §15 embedding
backfill and nightly re-embedding. One-off cost, no standing charge.

### 6.4 Guardrails

`ApplyGuardrail` evaluates text standalone, so one policy screens **both** the Qwen and Bedrock
paths. For a product collecting budget and personal circumstances in free text, PII redaction is
the one Bedrock feature that is genuinely hard to build yourself. Priced per text unit — opt in
when there is a launch date, not before.

## 7. Configuration and IAM

As implemented in step 1:

```python
# Region for both Bedrock clients. Required: neither boto3 nor the Anthropic Bedrock
# client applies a default. Credentials are resolved by the standard boto3 chain and
# so are not repeated in Settings.
aws_region: str = ""

bedrock_chat_model: str = "anthropic.claude-sonnet-5"
bedrock_effort: str = "low"
bedrock_disable_thinking: bool = True
bedrock_embedding_model: str = "cohere.embed-english-v3"
bedrock_embedding_batch_size: int = 96
bedrock_input_cost_per_1m: float = 0.0
bedrock_output_cost_per_1m: float = 0.0
```

> Deviation from earlier drafts: `aws_access_key_id` / `aws_secret_access_key` /
> `aws_session_token` are **not** Settings fields. Boto3 and the Anthropic Bedrock client already
> resolve credentials from the standard chain, so declaring them would duplicate credential
> handling. Only `aws_region` is configured, because it genuinely has no default.

| Environment | Credentials |
|---|---|
| Local dev | `~/.aws/credentials` profile or `.env` |
| **Vercel** | Dedicated IAM **user** key pair in project env vars |

Least-privilege policy, resources enumerated — the guardrail that stops a config typo from
invoking a far more expensive model:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:<region>::foundation-model/cohere.embed-english-v3",
        "arn:aws:bedrock:<region>::foundation-model/anthropic.claude-sonnet-5"
      ] },
    { "Effect": "Allow", "Action": ["lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:<region>:<acct>:function:qwen-inference-prod" }
  ]
}
```

### Dependencies

```
anthropic[bedrock]>=0.40.0
boto3>=1.35.0
```

In **both** `pyproject.toml` and `requirements.txt` — the Vercel runtime installs from
`requirements.txt` and they are hand-synced. `llama-cpp-python` lives in the Lambda container
image, not in the backend's dependencies.

⚠️ **Cold-start budget.** `boto3` + `botocore` add ~15–20 MB to a Vercel bundle already carrying
`openai`, `supabase`, `sqlalchemy`, `asyncpg`. Measure; if it hurts, import `boto3` lazily inside
the provider constructors.

## 8. Error mapping

Implemented in step 2.

| Condition | Raiser | HTTP |
|---|---|---|
| `aws_region` unset | `raise_bedrock_not_configured` | 503 |
| Model access not enabled (403) | `raise_bedrock_access_denied` | 503 |
| Throttling / `RateLimitError` | `raise_bedrock_rate_limited` | 503 |
| Timeout (either SDK) | `raise_bedrock_request_timeout` | 504 |
| Any other upstream failure | `raise_bedrock_api_error` | 502 |
| `ValidationError` on the reply | `raise_bedrock_completion_parse_failed` | 502 |
| `stop_reason == "refusal"` | `raise_bedrock_structured_refusal` | 502 |
| `stop_reason == "max_tokens"` | `raise_bedrock_structured_reply_incomplete` | 502 |

Chat and embeddings reach Bedrock through different SDKs, so `BedrockTimeout` and
`BedrockCallFailure` union both. User-facing copy is identical across providers — pinned by a test.

## 9. Telemetry

Keep the `llm_call` record compatible with `openrouter.py:89-101` so SolarWinds ingestion and
existing dashboards survive:

```
provider="qwen"|"bedrock"|"openrouter", model=..., task="intake_parse",
outcome=..., duration_ms=..., prompt_tokens=..., completion_tokens=...,
total_tokens=..., cache_read_input_tokens=..., estimated_cost_usd=...,
fallback_used=false, model_version="qwen-ft-2026-01"
```

`task` and `model_version` are what let you answer "did the retrain regress intake parsing?"
without a deploy.

## 10. Testing

Every provider takes an injectable client, so no network access is required.

| Test | Asserts |
|---|---|
| `test_routing::test_task_routes_to_configured_provider` | each `LlmTask` → the right provider |
| `test_routing::test_infra_error_triggers_fallback` | timeout/5xx → fallback called once |
| `test_routing::test_validation_error_does_not_fallback` | parse failure → raises, no second call |
| `test_bedrock_chat::*` | ✅ 16 tests — system split, temperature dropped, thinking off, stop-reason mapping, error mapping |
| `test_exceptions::test_user_facing_copy_does_not_vary_by_provider` | ✅ copy pinned across providers |
| `test_bedrock_embeddings::test_batches_and_preserves_order` | 200 texts → chunked, input order |
| `test_qwen_lambda::test_temperature_forwarded` | Qwen **does** get `temperature` |

Plus a **grammar conformance test in the Lambda image build**: generate N outputs from the real
model under the grammar and assert every one validates. That is the check that catches a schema
change silently breaking §5.3.

---

# Part II — Scaling within the free tier

## 11. What actually needs fixing

| Limitation today | Consequence |
|---|---|
| `find_similar_listings` embeds up to **101 texts per request** | Re-embeds the same listings forever; cost and latency scale with pool size |
| No queue | A slow provider call becomes a user-visible 5xx |
| No caching | Every identical prompt pays full price |

**§15 is the highest-impact item in this document and costs nothing.** Note what is *not* on this
list: model capacity. A 0.5B on Lambda scales horizontally by default, and Bedrock quotas only
bind the embedding path.

## 12. Capacity

The ceiling is **Lambda account concurrency** (default ~1,000 per region, raisable), not GPU
capacity or a quota you must negotiate.

```
peak_requests_per_sec × seconds_per_request  =  concurrent executions needed
```

At ~2 s per intake parse, 1,000 concurrency serves **~500 requests/sec** — far beyond plausible
near-term traffic. Request an increase when approaching it. That is the whole capacity plan.

## 13. Runtime stays on Vercel

The API tier does not move. Vercel already provides the edge, TLS, deploys, and preview
environments, and moving to Fargate + ALB + NAT would add roughly **$70/month** to run the same
code.

What this means concretely:

- **No VPC.** Lambda functions run outside a VPC and reach Bedrock and each other over
  IAM-authenticated public endpoints. No NAT Gateway, no VPC endpoints to configure.
- **No RDS Proxy.** Supabase's pgbouncer transaction mode already handles connection pooling, and
  `db_serverless` (`config.py:22-27`) is already wired for it.
- **No in-process model hosting.** §5.6's "fold the 0.5B into the API container" endgame requires a
  long-lived container; on Vercel the model stays in its own Lambda. That is fine — it is free
  either way.

§21 records what would justify revisiting this.

### 13.1 The Lambda inventory

| Function | Trigger | Job | Phase |
|---|---|---|---|
| `listing-ingest` | S3 `ObjectCreated` on `raw-listings/` | Normalise feed → upsert Postgres row → enqueue embed | B |
| `embed-worker` | SQS | Bedrock Cohere v3 → write vector to pgvector | B |
| `batch-manifest-builder` | EventBridge (nightly) | Pending listings → JSONL → S3 → `CreateModelInvocationJob` | B |
| `batch-result-loader` | EventBridge (job completion) | Read S3 results → write vectors | B |
| **`qwen-inference`** | `lambda:Invoke` from the API | **Run the 0.5B, return grammar-constrained JSON** | E |
| `qwen-warmer` | EventBridge, every 5 min | Keep one environment warm (§5.4) | E |

All within the free tier. Two constraints:

- **Cap event-source concurrency** on `embed-worker` so Lambda's willingness to scale cannot
  outrun the Bedrock quota.
- **Idempotency keys** (a unique column in Postgres, or DynamoDB's free tier). SQS redelivery is
  normal; without a dedupe check a retry burns a second Bedrock call for a result you already have.

## 14. Queue and backpressure

SQS is free to 1M requests/month — comfortably beyond current volume.

```
        Vercel (Next.js frontend + FastAPI backend)
                            │
        ┌───────────────────┼────────────────────┬─────────────────┐
        ▼                   ▼                    ▼                 ▼
┌───────────────┐  ┌─────────────────┐  ┌───────────────┐ ┌────────────────┐
│ Lambda        │  │ Bedrock         │  │ OpenRouter    │ │ Supabase       │
│ qwen-         │  │ cohere-v3       │  │ llama-3.1-8b  │ │ Postgres       │
│ inference     │  │ Guardrails      │  │ (3 chat paths)│ │ + pgvector     │
└───────────────┘  │ batch           │  └───────────────┘ └────────────────┘
                   └─────────────────┘                             ▲
        ┌───────────────────────────────────────────────┐          │
        │  S3 raw-listings/ ─▶ Lambda listing-ingest    │──────────┘
        │           └─▶ SQS ─▶ Lambda embed-worker ─────┼──▶ Bedrock
        │                        └─▶ DLQ (alarmed)      │
        └───────────────────────────────────────────────┘
```

| Class | Path | Under pressure |
|---|---|---|
| **Interactive** — intake parse, opening question | Sync → Qwen Lambda / OpenRouter | Bounded retry; then fallback (§3.3); then degrade |
| **Deferred** — embedding ingest and backfill | SQS → Lambda → Bedrock | Queued. No user impact |

Fit explanation and outreach draft stay synchronous for now — moving them behind SQS needs a
job-status endpoint and client polling, which is real product work. §21 records the trigger.

Mechanics: visibility timeout > worst-case latency; `maxReceiveCount` → DLQ + CloudWatch alarm;
capped event-source concurrency; idempotency keys.

## 15. Vector search on pgvector — the biggest win, for $0

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
                                   │ Supabase Postgres  │
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
                                   │ properties.embedding             │
                                   │ vector(1024) + HNSW index        │
                                   │ — same Postgres, no new service  │
                                   └──────────────────────────────────┘

  Backfill: EventBridge ─▶ batch-manifest-builder ─▶ S3 ─▶ Bedrock BATCH
                             ─▶ S3 results ─▶ batch-result-loader ─▶ Postgres


QUERY  (request path — one embedding call, regardless of corpus size)

┌────────────┐   ┌────────────────┐   ┌──────────────────────────────────────┐
│ seed       │──▶│ 1 embed call   │──▶│ pgvector k-NN                        │
│ listing    │   │ (Bedrock)      │   │ WHERE state/city/property_type match │
└────────────┘   └────────────────┘   │ ORDER BY embedding <=> $1 LIMIT k    │
                                      └──────────────────────────────────────┘
```

| | Today | With ingest-time embeddings |
|---|---|---|
| Embedding calls per request | up to **101** | **1** |
| Similarity | Python, over a 40–100 row pool | HNSW index, over the whole corpus |
| Quality | capped by the pre-filtered pool | true nearest neighbours corpus-wide |

The quality gain is not incidental: `DEFAULT_CANDIDATE_POOL = 40` means the true nearest neighbour
may never enter the ranking at all.

**pgvector, not OpenSearch.** The win is *ingest-time embedding*, not the index technology.
pgvector lives in the Postgres you already pay for; OpenSearch Serverless would add ~$350–700/month
for the same result at this corpus size. §21 records the trigger for revisiting.

**No `VectorIndex` protocol.** With a single implementation, an abstraction layer would be
speculative. Put the upsert and k-NN query in `app/repositories/properties.py` alongside the
existing `list_similar_candidate_rows`, matching how the rest of the codebase is organised. Extract
a protocol only if a second store ever appears.

**Migration:** add a `vector(1024)` column and an HNSW index, then backfill through Bedrock batch
(§6.3). Dimension is fixed by the model; changing it later means a full re-index, so treat that
choice as durable.

## 16. Caching without ElastiCache

| Layer | Where | Cost |
|---|---|---|
| **Opening-question cache** | Postgres table keyed by question row + prompt hash | $0 |
| **Circuit breaker state** (§3.3) | In-process per instance | $0 |
| **Bedrock prompt caching** | `cache_control` on stable prefixes, if Bedrock chat is ever routed | $0 |
| CloudFront / edge cache | Vercel already provides it | included |

In-process breaker state is less precise than a shared one — each serverless instance learns
independently that the Qwen function is down. At this volume that is an acceptable trade for
avoiding a standing ~$15/month, and the failure mode is mild (a few extra failed calls before each
instance trips).

The opening-question path is the only genuinely cacheable one — it is deterministic given a
question row. Intake parse is user-specific and will rarely hit.

## 17. Data layer

Supabase Postgres stays the system of record, and now also the vector store (§15).

`db_serverless` already enables NullPool and disables prepared statements for pgbouncer transaction
mode (`config.py:22-27`) — the connection-pooling problem is already solved for Vercel's execution
model. No RDS Proxy, no Aurora migration.

`qwen-inference` touches no database at all, which is one more reason the model-on-Lambda /
API-on-Vercel split stays clean.

## 18. Storage — S3 and ECR

Model weights ship **inside the Lambda container image**, which lives in **ECR**, not S3. The image
digest *is* the version, so **rollback = redeploy the previous tag**.

| Store | Contents | Cost |
|---|---|---|
| **ECR** | `qwen-inference` images — weights, runtime, grammars | ~$0.10–0.20/mo |
| S3 `raw-listings/` | Ingestion feed; triggers `listing-ingest` | cents |
| S3 `batch-inference/{input,output}/` | Transport for Bedrock batch (§6.3) | cents, expire after days |
| S3 `eval/golden-sets/` | Fixed intake prompts + expected criteria — the retrain gate | negligible |

**Not doing yet:** `model-invocation-logs/` and inference capture. Beyond the CloudWatch cost,
those record **full prompts and completions** — for this product that means budget, location, and
personal circumstances. Enabling capture "for debugging" and forgetting creates a durable PII store
nobody scoped. If it is ever enabled: sample, set a lifecycle expiry, encrypt with SSE-KMS,
restrict read access separately, and run Guardrails redaction *before* the write.

## 19. Observability

CloudWatch Logs is free to 5 GB/month ingest — adequate, with retention set.

- Lambda metrics: duration, billed duration, concurrent executions, cold-start rate, errors,
  throttles.
- Keep the existing SolarWinds shipping (`swo_logs_url`) and the `llm_call` shape (§9).
- **Skip X-Ray and Firehose/Athena for now** — both add cost for observability the current volume
  does not need.

Alarms that matter: **`fallback_used` rate**, Qwen p99 duration and cold-start rate, Lambda
throttles, SQS depth and DLQ depth, Bedrock error rate.

**Abuse control:** per-tenant budgets enforced in application code — the defence against one
account or a compromised key consuming the Bedrock budget. Pure application logic; nothing in AWS
does it for you, and it costs nothing to add.

## 20. Cost summary

| Component | Monthly |
|---|---|
| Lambda (`qwen-inference` + workers + warmer) | **$0** — perpetual free tier |
| SQS | **$0** — perpetual free tier |
| pgvector | **$0** — existing Supabase |
| CloudWatch Logs | **~$0** — 5 GB free |
| S3 | **cents** |
| ECR | **~$0.10–0.20** |
| Bedrock embeddings | **cents** — ~$0.00002/search after §15 |
| OpenRouter (3 chat paths) | current bill, ~$0 |
| **Total added** | **under ~$1/month** |

One-off: the embedding backfill through Bedrock batch, priced by corpus size at ~50% of on-demand.

Largest savings levers, already applied: ingest-time embeddings (§15), pgvector over OpenSearch
(§15), Vercel over Fargate+NAT (§13), in-process caching over ElastiCache (§16), and keeping the
three general chat paths on OpenRouter (§3.1).

## 21. Deferred decisions and their triggers

Recorded so the reasoning is not lost, and so the trigger is explicit rather than a vibe.

| Deferred | Cost if adopted | Adopt when |
|---|---|---|
| **OpenSearch Serverless** | ~$350–700/mo floor | pgvector HNSW maintenance degrades write throughput on the primary, **or** hybrid keyword+vector search becomes a product requirement |
| **Fargate + ALB + NAT** | ~$70/mo | Vercel's function timeout or bundle limit blocks a needed feature, **or** you want the 0.5B in-process to remove a network hop |
| **ElastiCache** | ~$15/mo | Per-instance circuit breakers cause visible flapping, **or** a shared rate limiter becomes necessary for per-tenant budgets |
| **Bedrock chat (Sonnet 5)** | ~$30/mo | OpenRouter output quality on fit/outreach measurably hurts conversion |
| **Fit/outreach behind SQS** | $0 infra, real product work | p95 latency on those endpoints becomes a complaint |
| **X-Ray, Firehose/Athena** | usage-based | Debugging a latency problem that CloudWatch cannot explain |
| **Multi-region** | doubles most line items | A stated availability SLO |

## 22. Rollout

| Phase | Work | Cost |
|---|---|---|
| **A — Routing layer** ← *steps 1–7* | Bedrock providers, `routing.py`, `LlmTask`, `task=` on 4 call sites, fallback + breaker. Every route still OpenRouter/HF | $0 |
| **B — Ingest-time embeddings** | `vector(1024)` column + HNSW, repository upsert/k-NN, ingest Lambda, SQS, backfill, rewrite `find_similar_listings` | $0 |
| **C — Bedrock embeddings** | Route embeddings to Cohere v3 | cents |
| **D — Qwen on Lambda** | Container image, GBNF grammars, `qwen_lambda.py`, warmer, memory tuning; route `intake_parse` | $0 |
| **E — Guardrails** | `ApplyGuardrail` on intake input/output before launch | per text unit |

**A and B are free and account for most of the value.** They are worth completing even if C, D and
E never happen.

## 23. Open questions

1. **Quantisation and measured latency** — which GGUF quant, and p50/p99 at 3,008 MB on a real
   intake prompt? Every number in §12 and §20 follows from this. Benchmark before phase D.
2. **Does the grammar path hold?** (§5.3) The single largest technical risk. Prove it against the
   real schemas early.
3. **Retrain promotion gate** — a golden set in `eval/golden-sets/` and a pass threshold, so
   `model_version` telemetry (§9) has something to gate on.
4. **Cold start tolerance** — is a few-second p99 on the first request after idle acceptable?
5. **Listing corpus size** — decides whether pgvector HNSW is comfortable and when §21's OpenSearch
   trigger might fire.
