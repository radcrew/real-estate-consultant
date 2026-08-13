# Serving the intake model

Two files here. `serve_local.py` runs the model on your machine for evaluation;
`llama-server.service` runs it on a host for production. Same binary, same flags — the
difference is supervision, TLS and a credential.

**The artifact to ship is `qwen2.5-0.5b-instruct-intake-q4_k_m.gguf`** — the plain Q4
quant, not the imatrix one. See `pipeline/eval/results.md`: the imatrix scored 0.901 against
0.935 and costs an hour per build.

## The shape of the deployment

```
Browser → Next.js → FastAPI on Vercel ──HTTPS──→ router.huggingface.co/v1
                    (stateless fn)      │        (outreach, fit, opening question)
                                        └──────→ your box: TLS proxy → llama-server
                                                 (intake extraction only)
```

The Vercel function cannot hold the model: no persistent RAM between invocations, a
bundle limit well under 398 MB, and a cold start per request. The long-lived process is
not a workaround for that — it is the point. Only a process that survives between
requests keeps the ~929-token constant prompt prefix cached, and that is a large part of
why intake is fast at all.

## Sizing the box

| Need | Figure |
|---|---|
| Weights | 398 MB, resident |
| KV cache | ~12 KB/token; 4096 ctx × 1 slot is ~50 MB |
| RAM | 2 GB is comfortable |
| Disk | 2 GB including the binaries |

**Cores decide latency, so size from measurement, not from the RAM figure.** Measured on
6 physical cores: p50 1262 ms, p95 1801 ms. Throughput scales roughly with cores here, so
a 2-vCPU box lands nearer 3–4 s per turn. Run `llama-bench` on the candidate before
committing, and compare against the 75 s client read timeout with a wide margin — the
number that matters is what users feel, not what fits.

Put the box in the same region as the Vercel function. At these latencies a cross-region
round trip is no longer negligible.

## Deploying

1. **Build the binaries** on the host (`cmake`) or copy a release build to
   `/opt/llama.cpp`. No Docker.
2. **Copy the GGUF** to `/opt/models/`. Ship it via the Hub or object storage, never git.
3. **Create the credential** — its own value, not `HF_TOKEN`:
   ```bash
   printf 'LLAMA_API_KEY=%s\n' "$(openssl rand -hex 32)" | sudo tee /etc/llama-server.env
   sudo chmod 600 /etc/llama-server.env
   ```
4. **Install the unit**: copy `llama-server.service`, then
   `sudo systemctl daemon-reload && sudo systemctl enable --now llama-server`.
5. **Terminate TLS in front of it.** The unit binds `127.0.0.1` deliberately; a bearer
   token must not cross the internet in clear. Caddy is two lines:
   ```
   llm.example.com {
       reverse_proxy 127.0.0.1:8080
   }
   ```
   Vercel's egress IPs are dynamic, so an IP allowlist is not available — the API key and
   TLS are the whole perimeter.
6. **Point the backend at it**, in the Vercel dashboard:
   ```
   INTAKE_CHAT_MODEL=qwen2.5-0.5b-instruct-intake
   INTAKE_CHAT_BASE_URL=https://llm.example.com/v1
   INTAKE_CHAT_API_KEY=<the LLAMA_API_KEY value>
   ```
   Only `parse_user_input` reads these. Outreach, fit explanations and the opening
   question stay on the router, so a small extraction model never writes prose.

## Verifying

```bash
# The alias must match INTAKE_CHAT_MODEL exactly.
curl -H "Authorization: Bearer $KEY" https://llm.example.com/v1/models

# Then score the deployed endpoint with the same harness used for every other row.
cd services/intake-model
python -m pipeline.eval.run --label 0.5b-lora-q4km-prod --split all --no-next-question \
  --base-url https://llm.example.com/v1 --api-key "$KEY" \
  --model qwen2.5-0.5b-instruct-intake
```

A production row that disagrees with `0.5b-lora-q4km-local` means the deployment differs
from what was measured — wrong artifact, wrong flags, or a proxy rewriting requests.
Chase it before trusting the box.

## Rolling back

Clear the three `INTAKE_CHAT_*` variables and redeploy. Intake returns to the router.
No code revert, which is why nothing about the URL or model id is hardcoded.

## Known gaps

- **Nothing monitors the box.** Intake now degrades to the router on 502/503/504, so an
  outage is survivable but **silent** — the only trace is a `intake_endpoint_fallback`
  warning in the logs. Alert on that log line, on the systemd unit failing, and on the 5xx
  rate from the reverse proxy. A box that has quietly been down for a week, with every
  request going to the router at router prices, is the failure mode to watch for.
- **The fallback is deliberately narrow.** Only transport faults trigger it. A 401 from a
  wrong `--api-key`, or a 4xx from a malformed request, is raised rather than retried:
  those would fail identically on the router, so retrying would double the cost and hide a
  configuration error instead of surfacing it.
- **Concurrency is untested under load.** `--parallel 1` is sized for an internal MVP.
  Measure two simultaneous requests before assuming a second user is free.
