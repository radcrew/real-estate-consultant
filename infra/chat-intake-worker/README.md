# `chat-intake-worker` — queued intake turns

Consumes `chat-intake.fifo` and runs each turn through the same pipeline the API runs
inline (`app/services/intake_jobs.py`), writing the result to `public.intake_jobs`.

Nothing here is required to run the product. With `SQS_CHAT_QUEUE_URL` empty the endpoint
runs turns inline and the client contract is identical — this exists so a slow provider
becomes latency instead of a lost message.

## The cost this carries

This is a **second deployable running the same code**. Provider configuration and the
Supabase service-role key now live in two places, and drift between them is a failure
mode that did not exist before: a route pinned in Vercel but not here means the worker
quietly serves turns from a different model. Set them from one source when you can, and
`test_chat_intake_worker_packaging` fails if a newly-required setting is missing from
the list below.

## 1. Create the queue and its dead-letter queue

```bash
AWS_REGION=us-east-1
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

aws sqs create-queue --queue-name chat-intake-dlq.fifo \
  --attributes FifoQueue=true,ContentBasedDeduplication=false

DLQ_ARN=$(aws sqs get-queue-attributes \
  --queue-url https://sqs.$AWS_REGION.amazonaws.com/$ACCOUNT/chat-intake-dlq.fifo \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)

aws sqs create-queue --queue-name chat-intake.fifo --attributes '{
  "FifoQueue": "true",
  "ContentBasedDeduplication": "false",
  "FifoThroughputLimit": "perMessageGroupId",
  "DeduplicationScope": "messageGroup",
  "VisibilityTimeout": "180",
  "RedrivePolicy": "{\"deadLetterTargetArn\":\"'$DLQ_ARN'\",\"maxReceiveCount\":\"3\"}"
}'
```

Why these values:

| Setting | Value | Why |
|---|---|---|
| `FifoQueue` | true | Two turns of one session processed out of order overwrite each other's criteria — the user answers a question and watches the answer disappear |
| `ContentBasedDeduplication` | false | The publisher sets `MessageDeduplicationId` to the job id explicitly; content hashing would dedupe two genuinely different turns that happen to match |
| `FifoThroughputLimit` / `DeduplicationScope` | per message group | High-throughput mode. Ordering is only needed *within* a session, so sessions should not serialise against each other |
| `VisibilityTimeout` | **360s** | Must exceed the function timeout below, or a turn still being worked on is redelivered. The claim gate makes that harmless but it burns a receive, and three of those send a live turn to the DLQ |
| `maxReceiveCount` | 3 | Bounded redelivery, then the DLQ. Alarm on DLQ depth: anything landing there is a turn a user never got |

## 2. Roles

The API's publish role and the worker's execution role are separate: the API has no
reason to consume the queue, and splitting them means a compromised Vercel key cannot
drain pending turns.

Worker execution role needs `sqs:ReceiveMessage`, `sqs:DeleteMessage`,
`sqs:GetQueueAttributes` on `chat-intake.fifo`, plus whatever its routed providers need —
`lambda:InvokeFunction` on `qwen-inference-prod` if intake parse is routed to Qwen, or
`bedrock:InvokeModel` if it is routed to Bedrock. Grant only the route actually in use;
the architecture doc §7 has the policy documents.

## 3. Build and push

```bash
REPO=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/chat-intake-worker
aws ecr create-repository --repository-name chat-intake-worker --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Context is backend/, not this directory.
docker build --platform linux/amd64 \
  -f infra/chat-intake-worker/Dockerfile \
  -t $REPO:$(git rev-parse --short HEAD) backend
docker push $REPO:$(git rev-parse --short HEAD)
```

## 4. Create the function

```bash
aws lambda create-function \
  --function-name chat-intake-worker-prod \
  --package-type Image \
  --code ImageUri=$REPO:<tag> \
  --role arn:aws:iam::$ACCOUNT:role/chat-intake-worker-exec \
  --memory-size 1024 \
  --timeout 300 \
  --environment "Variables={$(cat <<'VARS'
DATABASE_URL=...,SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...
VARS
)}"
```

**Required environment variables** — these have no defaults, so the module fails to
import without them:

- `DATABASE_URL` — required by `Settings` even though this worker only uses PostgREST.
  A placeholder is enough, but it must be present.
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`

Then whatever the routed providers need: `OPENROUTER_API_KEY` (the next-question call on
every turn), `AWS_REGION` and the `LLM_ROUTE_*` pins, `QWEN_INFERENCE_FUNCTION_NAME`.
**The route pins must match Vercel's**, or the same turn gets different models depending
on which path ran it.

⚠️ **`BEDROCK_GUARDRAIL_*` must match too, if you use it.** Input screening happens in the
API before the row is written, so the worker never repeats it — but *output* screening
runs inside the turn, which means it runs here. An unset `BEDROCK_GUARDRAIL_ID` (or a
missing `AWS_REGION`) makes screening a silent pass-through, so a worker configured
differently from Vercel would quietly stop screening what the API screens. Nothing errors;
the frames just stop being checked.

**These timeouts form an ordered chain**, and each link must clear the one before it:

```
worst-case provider call  <  function timeout  <  visibility timeout  <  CHAT_JOB_STALE_AFTER_SECONDS
        ~265s                      300s                 360s                        420s
```

The provider end is larger than it looks and is what sets the floor: OpenRouter alone is
a 75s read timeout with 3 retries (~225s), plus output guardrail screening if enabled.
Size the function timeout from *that*, not from how long a turn usually takes — a healthy
turn is seconds, and these numbers exist for the tail.

Break the ordering and the failures are quiet: a function timeout under the provider
worst case kills live turns, which the claim gate then stops redelivery from retrying; a
visibility timeout under the function timeout redelivers turns that are still running,
burning receives until a live turn lands in the DLQ.

## 5. Wire the event source, with a cap

```bash
aws lambda create-event-source-mapping \
  --function-name chat-intake-worker-prod \
  --event-source-arn arn:aws:sqs:$AWS_REGION:$ACCOUNT:chat-intake.fifo \
  --batch-size 5 \
  --function-response-types ReportBatchItemFailures \
  --scaling-config MaximumConcurrency=10
```

- `ReportBatchItemFailures` is **not optional**. Without it a single failed turn redrives
  its whole batch, re-running turns that already succeeded — and the claim gate turns
  those into no-ops, so the user's later turns simply stall.
- `MaximumConcurrency` caps how hard the queue can push the provider. Uncapped, the
  queue's only effect under load is to deliver the overload faster.

## 6. Turn it on

Set `SQS_CHAT_QUEUE_URL` in Vercel. That is the switch: until then the API runs turns
inline and this function sits idle. To roll back, clear the variable — in-flight jobs
finish on the worker and new turns go back to running inline.

## Verifying

```bash
# Insert a queued job row, then invoke with its ids.
aws lambda invoke --function-name chat-intake-worker-prod \
  --payload file://infra/chat-intake-worker/sample-event.json /dev/stdout
```

A healthy run returns `{"batchItemFailures": []}` and leaves the row `succeeded`. An
`itemIdentifier` in the response means the turn is going back on the queue.

## Alarms worth having

- **DLQ depth > 0** — every message there is a turn a user never received.
- **Queue age of oldest message** — the backlog signal that matters to a waiting user.
- **`attempts` climbing on `intake_jobs`** — a redelivery loop, visible before the DLQ.
- **Lambda throttles** — the concurrency cap is working, or the provider is the limit.
