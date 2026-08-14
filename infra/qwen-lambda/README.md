# `qwen-inference` — Qwen2.5-0.5B on Lambda

CPU-only container that serves criteria extraction for the intake path, and nothing
else. `app/llm/providers/qwen_lambda.py` invokes it over IAM; the two sides of the
payload contract are tested together in `backend/tests/infra/test_qwen_handler.py`.

Free tier is perpetual — 1M requests and 400,000 GB-seconds a month — so at roughly
3 GB × 2 s per call this is about 65,000 calls/month at no cost.

## 1. Put the weights in place

```
infra/qwen-lambda/model/qwen.gguf
```

The GGUF is never committed (see `.gitignore`); the image digest is what versions it.

**Which weights** is an open decision. The plan assumes a Qwen2.5-0.5B *fine-tuned on
criteria extraction*; no such artifact is in this repo. Base `Qwen2.5-0.5B-Instruct`
will run and — because generation is grammar-constrained — will always return valid
JSON, but a 0.5B that has not seen this task will fill it in noticeably worse. Decide
before trusting the numbers in the architecture doc's §12 and §20.

Quantisation is also unmeasured. `Q8_0` is the conservative starting point; `Q4_K_M`
roughly halves the image and speeds generation at some accuracy cost. Benchmark both
against real intake prompts (architecture doc §23.1).

## 2. Regenerate the schemas if a model changed

```bash
cd backend && python scripts/export_qwen_schemas.py
```

`build_grammars.py` compiles `schemas/*.json` into GBNF during the build, so the
decoder physically cannot emit JSON that violates the envelope. A Pydantic model edited
without re-exporting leaves the grammar on the old shape and the new field silently
never appears — `tests/infra/test_qwen_schema_export.py` fails on that drift.

Note the grammar constrains the *envelope* only. `extracted` is an open object because
question keys live in the database, so the backend still validates its contents against
the questions that actually exist.

## 3. Build and push

```bash
AWS_REGION=us-east-1
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REPO=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/qwen-inference

aws ecr create-repository --repository-name qwen-inference --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

docker build --platform linux/amd64 -t $REPO:$(git rev-parse --short HEAD) .
docker push $REPO:$(git rev-parse --short HEAD)
```

`--platform linux/amd64` matters on an ARM workstation: Lambda runs the architecture the
image was built for, and the mismatch surfaces as a runtime error, not a push failure.

## 4. Create the function

```bash
aws lambda create-function \
  --function-name qwen-inference-prod \
  --package-type Image \
  --code ImageUri=$REPO:<tag> \
  --role arn:aws:iam::$ACCOUNT:role/qwen-inference-exec \
  --memory-size 3008 \
  --timeout 30 \
  --region $AWS_REGION

# Cost blast-radius cap: without this, a runaway caller can consume account concurrency.
aws lambda put-function-concurrency \
  --function-name qwen-inference-prod --reserved-concurrent-executions 20
```

**No VPC.** The function talks to nothing but its caller, and staying outside a VPC
avoids a NAT Gateway — the single largest avoidable cost in a deployment this shape.

Memory is a speed/cost trade, not just a ceiling: Lambda scales vCPU with memory, so a
larger setting can finish sooner and cost less overall. Run Lambda Power Tuning across
1,769 / 3,008 / 5,120 MB with a real intake prompt and pick from the measured curve.

## 5. Keep one environment warm

Cold start is container init plus model load — seconds, even with `mmap`. An EventBridge
rule every 5 minutes is ~8,600 invocations/month, inside the free tier:

```bash
aws events put-rule --name qwen-warmer --schedule-expression "rate(5 minutes)"
```

Point it at the function with a payload the handler rejects cheaply, or add a
`{"warm": true}` short-circuit if the rejection cost ever shows up in the logs.
Provisioned concurrency bills continuously and defeats the reason Lambda was chosen.

## 6. Route traffic to it

In the backend environment:

```
AWS_REGION=us-east-1
QWEN_INFERENCE_FUNCTION_NAME=qwen-inference-prod
QWEN_MODEL_VERSION=qwen-ft-2026-01     # free-text, recorded on every llm_call
LLM_ROUTE_INTAKE_PARSE=qwen
```

The caller's IAM policy needs `lambda:InvokeFunction` on this function's ARN and nothing
more. Intake parse routes here and only here: the fine-tune knows one task's schema, so
there is deliberately no fallback to another model — a general model would return a
differently-shaped answer that still validates, which is worse than an honest error.
