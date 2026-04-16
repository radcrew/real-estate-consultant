# AI-Powered Commercial Real Estate Search Assistant

**Product type:** Internal MVP (not a public LoopNet-style marketplace).

**North star:** A system that behaves like a capable virtual CRE agent: qualify the search, gather listings from lawful sources, normalize and reason over properties, rank by fit, support saved workflows, and draft broker outreach for human approval.

---

## Table of contents

1. [Summary](#summary)
2. [Positioning](#positioning)
3. [Core use case](#core-use-case)
4. [MVP pillars](#mvp-pillars)
5. [Architecture principles](#architecture-principles)
6. [Stack guidance](#stack-guidance)
7. [Project artifacts](#project-artifacts)
8. [Detailed documents](#detailed-documents)

---

## Summary

Help users find **industrial, flex, and retail** properties **for sale or lease** across the U.S., with emphasis on:

- Smart intake (broker-style qualification questions)
- Broad search across **lawful, publicly accessible** listing sources and related public data
- Candidate identification and **fit-based ranking**
- **Saved searches and watchlists**
- **Draft** outreach to listing brokers (email and contact-form copy)—no autonomous sending in MVP

---

## Positioning

| In scope | Out of scope (MVP) |
|----------|-------------------|
| Internal tool, single primary user initially | Public marketplace, LoopNet clone |
| Modular ingestion for growth | Scraping prohibited or private sources |
| Code structure that can grow toward multi-tenant SaaS | Full CRM, billing, enterprise RBAC |

See [docs/out-of-scope.md](docs/out-of-scope.md) for a full exclusion list.

---

## Core use case

Representative criteria the product should support well:

| Dimension | Example |
|-----------|---------|
| Property types | Industrial, flex, retail |
| Geography | Nationwide |
| Size | e.g. minimum building size 30,000+ SF |
| Physical | e.g. minimum clear height 22'+ as a hard requirement when specified |
| Ranking signals | Location quality, building size, clear height, ingress/egress, price, overall fit |

**Rule:** Treat user-defined criteria as **hard filters or deal-breakers** where the intake flow marks them as such; otherwise use them in ranking and explanation.

---

## MVP pillars

### 1. Intake / search understanding

Open with a **concise, broker-style** question set, for example:

- Property type  
- Sale vs lease  
- Market / geography  
- Minimum size, clear height  
- Loading / access and ingress/egress needs  
- Price or rent range  
- Special requirements  

Persist **search profiles / sessions** so one user can run multiple distinct searches.

### 2. Search and ingestion

Implement a **high-coverage, lawful** approach to marketed listings, combining techniques as appropriate:

- Public listing pages  
- Broker sites  
- Public documents / offering memorandum PDFs  
- Optional email-alert ingestion  
- Third-party data or browser automation (e.g. Apify-class tools) where terms allow  
- **Modular source connectors** so sources can be added or swapped  

Constraints: **no** LoopNet clone; **no** prohibited scraping patterns; architecture must support **adding or replacing sources** without rewriting the core app.

### 3. Property understanding

For each candidate:

- Extract structured fields from pages and public docs  
- Use an LLM layer to summarize fit and support scoring  
- Resolve **clear height** when possible from listings, brochures, public records, or (secondary) imagery—inference must be **labeled** vs explicit facts  
- Surface **uncertainty**: explicit vs inferred vs unknown  

### 4. Ranking

Produce a **prioritized shortlist** with clear rationale, weighted toward:

- Location quality  
- Building size  
- Clear height  
- Ingress/egress  
- Price  
- Overall fit  

### 5. Outreach (draft only)

- Email drafts to listing brokers  
- Contact-form draft text where relevant  

**MVP:** generation and editing only; **no** auto-send or auto-submit.

### 6. Saved workflows

- Saved searches  
- Favorites / watchlist  
- Shortlist view  
- Per-property notes and status  

---

## Architecture principles

- **Single admin user** for MVP; structure code and data so **multi-user SaaS** is a natural next step.  
- **Modular, readable** codebase; document boundaries between intake, ingestion, normalization, ranking, and outreach.  
- Stack is a **project decision**: prefer practical, maintainable, cost-conscious choices.

---

## Stack guidance

Illustrative options (not prescriptive):

- **Frontend:** React / Next.js  
- **Data:** Supabase or Postgres  
- **Acquisition:** Apify or similar where appropriate  
- **AI:** OpenAI, OpenRouter, or comparable LLM APIs  

---

## Project artifacts

Reasonable defaults for an internal MVP repo:

- Version-controlled **source**  
- **README** with local setup and environment variables  
- **Deployment** notes (hosting, migrations, secrets handling)  
- Short **admin** notes (auth, how to run ingestion, where configs live)  

---

## Detailed documents

| Document | Contents |
|----------|----------|
| [docs/mvp-scope.md](docs/mvp-scope.md) | Structured MVP scope (intake through technical setup) |
| [docs/out-of-scope.md](docs/out-of-scope.md) | Explicit MVP exclusions to prevent scope creep |

---

## Priorities (ranked)

1. Solid architecture and clear workflows  
2. Useful ranking and search experience  
3. Practical, lawful data ingestion  
4. Polish and enterprise completeness **after** the above  
