# Feature Ideas

Brainstormed additions for the AI-assisted CRE search app, grounded in what's already
here: Next.js frontend, FastAPI backend, a separate ingestion service with pluggable
connectors (`loopnet_seed` today), Supabase for data/auth, and OpenRouter-backed LLM
services for intake parsing and **draft-only** outreach. Grouped by theme, roughly in
order of "cheapest to bolt on" within each group.

---

## 1. AI features that build on the existing LLM layer

The intake (`backend/app/llm/intake`) and outreach (`backend/app/llm/outreach`)
services already do structured LLM extraction/generation. These reuse that pattern.

- **Fit explainability** — for each ranked listing, have the LLM produce a short
  "why this matches you" / "why this might not" narrative from the intake criteria
  vs. listing attributes, instead of (or alongside) a bare score.
- **Comparative Market Analysis (CMA) generator** — feed a shortlist + comps into
  an LLM prompt to produce a structured CMA report (price/SF, cap rate range,
  days-on-market) the consultant can hand to a client.
- **Negotiation prep brief** — draft-only (matches the outreach philosophy):
  likely counter-offer points, comps to cite, and questions to ask the broker,
  generated per listing.
- **Red-flag scanner** — summarize ingested listing docs/description text for
  zoning, environmental, flood-zone, or title-risk language worth flagging for
  follow-up.
- **Conversational intake** — replace/augment the questionnaire wizard with a
  chat-style intake using the same LLM schema extraction under the hood, for
  users who'd rather describe their needs in a sentence than fill a form.
- **Natural-language search bar** — "warehouse near I-95 under $2M with rail
  access" parsed into the same structured filters the search wizard produces.
- **Portfolio/multi-site fit analysis** — for businesses evaluating several
  locations at once, compare a set of saved listings against one expansion
  criteria set and rank the set, not just individual properties.

## 2. Ingestion & data enrichment

The ingestion service (`services/ingestion/app/connectors`) is built for adding
connectors; these are natural next ones plus enrichment steps in the pipeline.

- **More sources**: Crexi, county assessor/GIS parcel data, zoning maps.
- **Change detection & alerts**: diff on re-ingestion (price drop, status change,
  new listing matching a saved search) feeding a notification, not just a
  re-scrape.
- **Drive-time / isochrone enrichment**: geocode each listing and precompute
  drive-time radii (to highway access, labor pool centers, a client's other
  locations) as part of normalization.
- **Demographic overlay**: attach Census/foot-traffic-style data to retail
  listings for site-selection scoring.
- **Document ingestion**: accept an Offering Memorandum PDF and run LLM
  extraction to populate/verify structured fields instead of manual entry.

## 3. Search & discovery UX

- **Map-based search** with a drawable drive-time radius instead of just a
  list/grid.
- **Side-by-side comparison table** for shortlisted listings (spreadsheet-style,
  not just cards).
- **"Similar listings" recommendations** using the same fit-scoring logic as
  intake matching.
- **Saved-search alerts**: email/SMS digest when a saved search gets new or
  changed matches (pairs naturally with the ingestion change-detection idea).
- **Swipe-to-shortlist**: a quick Tinder-style pass over new listings for
  users who want a fast triage before a deeper look.

## 4. Collaboration & workflow

- **Deal rooms**: a shared workspace per engagement (client + consultant, maybe
  broker) with comments and a checklist, scoped to an intake session.
- **Shareable client report**: turn a shortlist + fit rationale into a
  read-only shareable link or PDF, for consultants to hand off without a login.
- **Tour scheduling**: calendar integration for booking property tours from a
  shortlist.
- **LOI drafting assist**: same draft-only pattern as outreach — generate a
  Letter of Intent skeleton from listing + intake terms, never auto-sent.

## 5. Outreach & pipeline tracking

- **Outreach status tracking**: lightweight kanban (drafted → sent → replied →
  scheduled) layered on top of the existing draft-outreach records — still no
  auto-send, just tracking what a human did with the draft.
- **Tone/template library**: multiple outreach voice presets (formal, casual,
  investor-to-investor) reusing the same generation service.
- **Broker response summarizer**: paste in a broker's reply and get a
  structured summary (price movement, availability, next steps).

## 6. Admin & analytics

- **Ingestion health dashboard**: connector success/failure rates, last-run
  times, records ingested — visibility into the pipeline already scaffolded
  under `app/admin/ingest`.
- **Questionnaire funnel analytics**: where users drop off in the intake
  wizard, to inform question ordering/wording.
- **Data freshness indicators**: surface "last verified" per listing in the UI
  so users know how stale a source listing might be.

## 7. Smaller/creative differentiators

- **Jargon mode**: a toggle that has the LLM explain CRE terms inline for
  first-time commercial tenants/buyers.
- **Weekly market pulse**: auto-generated newsletter content from ingestion
  trends (new supply, price movement by submarket), feeding the existing
  newsletter subscribe flow.
- **Site Selection Scorecard**: one headline number plus an expandable
  breakdown of the factors behind it (fit, price, drive-time, demographics),
  shown on both listing cards and detail pages.
- **Multi-language outreach drafts**: generate the same draft in a second
  language for international investors/tenants.

---

## Suggested starting point

If picking just one to prototype first: **Fit explainability** (§1) is the
smallest lift — it's a new prompt against data the intake/search pipeline
already produces — and it's the most visibly "smart" thing a user sees on
every results page.
