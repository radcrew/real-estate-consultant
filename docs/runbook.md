# Runbook — Backend Incident Response

Use this when the backend is down, degraded, or a synthetic check is firing.
Start at **Step 1** and work down until the issue is identified.

---

## Step 1 — Confirm the scope

| Check | How |
|-------|-----|
| Is it us or the platform? | Check [Vercel status](https://www.vercel-status.com) and [Supabase status](https://status.supabase.com) |
| Which endpoints are affected? | `curl -i https://<BACKEND_URL>/health/ready` — inspect the `checks` field |
| When did it start? | GitHub Actions → **Synthetics** workflow — first failed run timestamp |
| What version is live? | `curl https://<BACKEND_URL>/health/ready` → `git_sha` field, match against git log |

---

## Step 2 — Read the logs

1. Open the [Vercel dashboard](https://vercel.com/dashboard) → select the backend project.
2. Go to **Deployments** → click the active deployment → **Functions** → **Logs**.
3. Filter by `"level":"ERROR"` or `"message":"unhandled_exception"` to find the first
   failure in the window.
4. Note the `request_id` from the error event, then filter on that ID to see the full
   request trace (all log lines for that request share the same `request_id`).

Key log events and what they mean:

| Event | Meaning |
|-------|---------|
| `unhandled_exception` | Uncaught bug — check `error` and `exc_info` fields |
| `http_exception` + `status: 502` | Supabase PostgREST unreachable |
| `http_exception` + `status: 503` | HF API key missing or service down |
| `http_exception` + `status: 504` | HF API timed out |
| `/health/ready` check `db: fail` | Postgres unreachable or credentials wrong |
| `/health/ready` check `supabase: fail` | Supabase REST endpoint unreachable |

---

## Step 3 — Common causes and fixes

### DB unreachable (`db: fail` in `/health/ready`)

1. Verify `DATABASE_URL` is set correctly in Vercel → **Settings** → **Environment Variables**.
2. If using pgbouncer (port 6543), confirm `DB_SERVERLESS=true` is also set.
3. Check the Supabase project is not paused (free-tier projects pause after 1 week of
   inactivity) — **Supabase dashboard** → project → **Settings** → **General**.
4. If the project was paused and resumed, it may take ~30 s before connections are accepted.

### Supabase REST unreachable (`supabase: fail`)

1. Check [Supabase status](https://status.supabase.com) for a platform incident.
2. Confirm `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct in Vercel env vars.
3. If DDL was recently applied, PostgREST may have a stale schema cache — run
   `NOTIFY pgrst, 'reload schema';` in the Supabase SQL editor.

### HF / LLM routes failing

1. Confirm `HF_TOKEN` is set and valid (Hugging Face dashboard → Access Tokens).
2. Check [Hugging Face status](https://status.huggingface.co).
3. Check `hf_model` config matches an available model on the HF router.

### Environment variable missing

A `500 Internal Server Error` on startup is almost always a missing required env var
(`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).
Verify all vars from `backend/.env.example` are present in the Vercel project's
**Production** environment.

---

## Step 4 — Rollback procedure

### Via Vercel dashboard (fastest)

1. Vercel dashboard → backend project → **Deployments**.
2. Find the last known-good deployment (before the incident started).
3. Click **⋯** → **Promote to Production**.
4. Verify: `curl https://<BACKEND_URL>/health/ready` returns `"status":"ok"` and the
   `git_sha` matches the promoted deployment.

### Via Vercel CLI

```bash
# List recent deployments to find the target URL
vercel ls --scope <YOUR_SCOPE>

# Instant rollback to the previous production deployment
vercel rollback --scope <YOUR_SCOPE>

# Or promote a specific deployment by URL
vercel promote <DEPLOYMENT_URL> --scope <YOUR_SCOPE>
```

### Via GitHub (redeploy a previous commit)

```bash
git revert <bad-commit-sha>   # or git checkout <good-sha> -- relevant files
git push origin main          # triggers backend.yml → deploy + smoke test
```

---

## Step 5 — After the incident

1. Update the error-budget tracking in `docs/slo.md` (count failed synthetic probes).
2. If budget drops below 25 %, freeze non-critical deploys per the error-budget policy.
3. Write a brief post-incident note (what broke, root cause, fix, prevention) and add it
   as a comment to the GitHub issue or PR that caused the incident.
