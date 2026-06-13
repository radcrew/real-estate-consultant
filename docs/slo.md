# Service Level Objectives

Service targets for the real-estate consultant backend (Vercel serverless + Supabase).
Measured over a rolling 30-day window against the `/health/ready` synthetic checks
(`.github/workflows/synthetics.yml`, every 15 minutes).

---

## Availability SLO — 99.5 %

| Window | Allowed downtime |
|--------|-----------------|
| 30 days | ≈ 3 h 36 min |
| 7 days  | ≈ 50 min |
| 1 day   | ≈ 7 min |

**Error budget math (30 days)**

```
total minutes = 30 × 24 × 60 = 43 200
budget        = 43 200 × (1 − 0.995) = 216 minutes ≈ 3 h 36 min
probe period  = 15 min  →  budget ≈ 14 missed probes before breach
```

**What counts as downtime:** any 15-minute window in which `/health/ready` returns
non-200 or times out on all three retry attempts.

**What does NOT count:** scheduled Vercel maintenance announced >24 h in advance,
or Supabase platform incidents tracked on status.supabase.com.

---

## Latency SLO — p95 ≤ 3 s

All non-LLM API routes (auth, search, listings, account) must respond within **3 s**
at the 95th percentile as measured by the `duration_ms` field in structured logs.

LLM-backed routes (`/intake/…`, `/outreach/…`) are excluded from the latency SLO
because they depend on a third-party model endpoint (Hugging Face router);
they have a separate target of **p95 ≤ 90 s** and a `request_slow` warning log is
emitted automatically at 3 s.

---

## Error budget policy

| Budget remaining | Action |
|-----------------|--------|
| > 50 % | Normal development pace |
| 25 – 50 % | Prioritise reliability fixes over new features in next sprint |
| < 25 % | Freeze non-critical deployments; address root cause before next deploy |
| Exhausted | Incident review required; no production deploy until budget partially restores |

---

## Measuring compliance

Until a dedicated metrics backend is in place, compliance is approximated from:

1. **GitHub Actions** — count failed `Synthetics` workflow runs in the 30-day window.
   Each failed run = one 15-minute window of downtime.
2. **Vercel function logs** — filter structured logs for `"level":"ERROR"` or
   `status >= 500` in `request_completed` events.
3. **Supabase dashboard** — DB query latency and connection counts.

---

*Targets are internal and set for a single-admin MVP. Revisit thresholds before
opening the product to external users.*
