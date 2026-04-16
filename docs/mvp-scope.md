# MVP scope

Structured breakdown of the first release. Aligned with the [product spec](../spec.md).

---

## Phase 1 — MVP

### A. User intake

- Guided intake flow with CRE-oriented qualification questions  
- Persist **search profiles** and **search sessions**  
- Support **multiple concurrent or saved searches** for the initial single-user / admin scenario

### B. Listing ingestion layer

- **Modular** ingestion framework (connectors per source or source family)  
- Pull property data from **approved, publicly accessible** sources only  
- Support, as applicable: listing pages, broker websites, public documents, optional email-based alerts  
- **Normalize** all ingested records into **one canonical schema**  
- Design for **add/replace** of sources without changing core product logic

### C. Property intelligence

Extract and persist structured fields, including where available:


| Category            | Fields / behavior                                            |
| ------------------- | ------------------------------------------------------------ |
| Identity / location | Address, geography, property identifiers as available        |
| Commercial          | Property type, sale vs lease, size, price or rent            |
| Physical            | Clear height, loading / access clues, ingress / egress hints |
| Parties             | Broker and contact information                               |
| Media / docs        | Links to supporting documents and images                     |


**LLM layer:**

- Summarize fit against the active search profile  
- Contribute to scoring / ranking narrative

**Data quality:**

- Mark fields as **explicit**, **inferred**, or **unknown**  
- Flag high-uncertainty inferences clearly in UI or API responses

### D. Search results and ranking

- **Ranked** results list (not an unordered dump)  
- **Property detail** view with sources, fields, and fit explanation  
- **Watchlist / favorites**  
- **Saved searches** (rerun or refresh as designed)  
- **Notes** and **status tags** on properties

### E. Outreach drafting

- Generate **email drafts** for listing brokers  
- Generate **contact-form** draft content where that pattern applies

**Constraint:** no automated send or form submission in MVP.

### F. Admin and technical foundation

- **Single-admin authentication** (or equivalent gate for internal MVP)  
- **SaaS-ready** layering: tenancy hooks, user model placeholders, config separation as appropriate  
- Documentation sufficient for **setup, deployment, and handoff** within the team

