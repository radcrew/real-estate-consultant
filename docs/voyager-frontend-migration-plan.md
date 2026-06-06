# Voyager → Real Estate Consultant: Frontend Migration Plan

> **Goal:** Apply the **Voyager** template's polished UI/design to the existing
> `frontend/` of the real-estate-consultant project, **without losing** the live
> backend integration, Supabase auth, and the AI intake → search → outreach
> workflow that already works.

## ✅ Confirmed decisions (locked)

| Decision | Choice |
|---|---|
| **Strategy** | **Full architecture + flow** (updated 2026-06-06) — adopt Voyager's page composition, component organization, and user flows, **wired to the existing data layer**. Goes beyond the earlier visual-reskin reading of "Option A". See §11 for the active plan. |
| **Scope / flows** | All four flows: **Home/discovery, Listings+map, Listing detail, Account workspace**. |
| **Data layer** | **Unchanged** — `services/`, `hooks/`, `contexts/`, `lib/` stay the source of truth; a thin adapter maps real data → Voyager component props. |
| **Theme** | **Light + dark** toggle, ported from Voyager. |
| **Animation** | **framer-motion** allowed (added to `frontend/`). |

> **Pivot note:** Steps 1–24 built the Voyager atom library (`components/ui/voyager/*`)
> and reskinned header/footer/hero/featured cards. Those atoms are the foundation
> for the architecture work; the reskinned sections may be recomposed into Voyager
> page sections during Phase B.

> **Non-negotiable:** No change to `services/`, `hooks/`, `contexts/`, `lib/`
> (Supabase + FastAPI), or the intake→search→outreach behavior. Only presentation
> (markup, styling, components, layout) changes.

---

## 1. The core problem in one sentence

`Voyager/` is a **good-looking but stack-incompatible booking template wired to
static demo data**, and `frontend/` is a **modern, backend-wired app with a plain
UI** — so we cannot just "swap folders." We have to **port Voyager's design into
`frontend/`**, upgrading each piece across two major framework gaps as we go.

---

## 2. Side-by-side reality check

| Concern | `frontend/` (keep this) | `Voyager/` (donor) | Conflict severity |
|---|---|---|---|
| Framework | **Next.js 16.2.4** (App Router) | Next.js 13.4 (App Router) | 🔴 Major — async `params`/`searchParams`, route APIs, `next/link` behavior, `typedRoutes` |
| React | **19.2.4** | 18.2 | 🟠 `use()`, ref-as-prop, effect timing differences |
| Styling | **Tailwind CSS v4** (CSS `@theme`, `globals.css`) | Tailwind CSS v3 (`tailwind.config.js`) + **SCSS** | 🔴 Config models are incompatible; Voyager ships `.scss` files |
| UI primitives | **shadcn + @base-ui/react + lucide-react** | Headless UI + Heroicons + `line-awesome` font icons | 🟠 Every component must be re-skinned/re-wired |
| Animation | (none) | **framer-motion 10** | 🟢 Additive, can adopt |
| Auth | **Supabase SSR** (`@supabase/ssr`) | **next-auth 4** | 🔴 Mutually exclusive — keep Supabase, drop next-auth |
| Data | **axios → FastAPI** (`/api/v1`) live | Static `src/data/*.ts` demo arrays + `StaticImageData` | 🔴 Domain models differ |
| Maps | Google Maps via env key (`use-location`) | `google-map-react` | 🟠 Different lib, same provider |
| Path alias | `@lib/* @services/* @components/* @hooks/* @contexts/*` | `@/*` → `src/*` | 🟠 Mechanical rewrite per file |
| Domain model | **Commercial RE**: `size_sqft`, `price`, `rent`, `clear_height`, `loading_docks`, broker fields | **Travel/residential**: `bedrooms`, `maxGuests`, `reviewStart`, `saleOff` | 🔴 Card/detail fields don't line up |
| Size | 87 `.tsx` | 250 `.tsx` + 34 `.ts` | — |

**Takeaway:** Voyager's value is its **visual language and component layouts**
(hero search, filter tabs, listing cards/grids, map+list split, account
workspace, modals). Its data layer, auth, and framework version are **not**
reusable as-is.

---

## 3. Strategy options

### Option A — Port Voyager UI *into* `frontend/` ✅ **Recommended**
Treat `frontend/` as the base of truth. Lift Voyager components one section at a
time, upgrade them to Next 16 / React 19 / Tailwind v4 / shadcn idioms, and wire
them to the **existing services/hooks**. Delete `Voyager/` at the end.

- ✅ Keeps the working backend, Supabase auth, modern stack, deploy pipeline.
- ✅ Incremental, reviewable, shippable section-by-section.
- ✅ No second framework/auth system to maintain.
- ⚠️ Each component needs hands-on porting (not copy-paste).

### Option B — Adopt Voyager as the base, graft backend in ❌
Make `Voyager/` the new frontend, then add Supabase + FastAPI + CRE model.

- ❌ Must upgrade Voyager Next 13 → 16 and React 18 → 19 anyway (same hard work).
- ❌ Re-implement *all* working business logic (intake, search, outreach, account).
- ❌ Rip out next-auth, rebuild Supabase SSR from scratch.
- ❌ Throws away the modern, already-correct stack. **Highest risk, most rework.**

### Option C — Two apps / iframe / micro-frontend ❌
Run both and stitch. Rejected: double deploy/auth/state surface, worst UX.

> **Decision: Option A.** The rest of this plan details it.

---

## 4. Target architecture (after migration)

```
frontend/
  app/                      # unchanged route groups, re-skinned pages
    (landing)/              # Voyager hero + featured grid look
    (auth)/                 # Voyager login/signup look, Supabase logic
    listings/               # Voyager filter-card grid + map split
    listings/[id]/          # Voyager listing-detail layout, CRE fields
    search/[id]/            # Voyager results UI on top of search service
    questionnaire/          # intake wizard, Voyager form styling
    account/                # Voyager "member workspace" layout
  components/
    ui/                     # shadcn primitives + ported Voyager shared/* (Button, Badge, Nav, Modal…)
    landing/ listings/ search/ account/ auth/   # re-skinned, same data props
  shared-ui/  (optional)    # home for generic ported Voyager atoms
  services/ hooks/ contexts/ lib/   # UNCHANGED — the data brain
  utils/ constants/
  app/globals.css           # Tailwind v4 @theme extended with Voyager design tokens
```

`Voyager/` is **removed from the repo** once porting is complete (it has its own
nested `.git`, `node_modules`, and lockfiles that must not ship — see §8).

---

## 5. Component & page mapping (Voyager → frontend)

| Voyager source | Target in `frontend/` | Notes |
|---|---|---|
| `src/shared/Button*.tsx`, `Badge`, `Input`, `Select`, `Checkbox`, `Textarea` | `components/ui/*` | Reconcile with existing shadcn primitives; keep one set, not two |
| `src/shared/Navigation/`, `Nav.tsx`, `Logo.tsx`, `MenuBar.tsx`, `SwitchDarkMode.tsx` | `components/landing/header` | Replace Heroicons with lucide; wire auth state from `contexts/auth` |
| `src/shared/NcModal.tsx`, `Pagination.tsx`, `NextPrev.tsx` | `components/ui/*` | framer-motion optional |
| `(home)/SectionGridFeatureProperty`, `SectionDowloadApp` | `components/landing/featured-listings`, hero | Feed real data from `listings`/`search` services |
| `(real-estate-listings)/SectionGridFilterCard`, `SectionGridHasMap`, `TabFilters` | `components/listings/*`, `components/search/result` | **Primary win.** Map demo `StayDataType` → `SearchProperty` |
| `components/PropertyCardH`, `StayCard`, `PropertyCard` | `components/listings/*-card` | Swap fields: beds/guests → `size_sqft`, `clear_height`, `loading_docks`, `rent/price`, broker |
| `(listing-detail)/*` | `app/listings/[id]` + `components/listings/detail` | Use `use-listing-detail` hook + gallery |
| `(account-pages)/*` + `config/brand.ts dashboard` | `app/account`, `components/account/sections` | Re-skin only; keep `account` service |
| `login/`, `signup/` | `app/(auth)/sign-in`, `sign-up` | UI only — **keep Supabase forms/logic** |
| `src/data/*.ts`, `authors.ts`, demo images | ❌ Do **not** port | Replaced by live services; keep a few placeholder images if needed |
| `next-auth`, `api/auth/*` | ❌ Drop | Supabase already owns auth |

### Domain-model adapter (the field mismatch)
Create `utils/listings/voyager-adapter.ts` to translate the live
`SearchProperty` into whatever prop shape the ported card components expect, so
we re-skin **without** rewriting every card's internals at once:

```
SearchProperty                         Voyager card prop
─────────────────────────────────────────────────────────
address/city/state            →        title / address line
property_type, listing_type   →        category badge
size_sqft                     →        primary spec chip
clear_height, loading_docks   →        spec chips (replace beds/baths)
price / rent                  →        price label
image / images[]              →        featuredImage / galleryImgs
latitude, longitude           →        map { lat, lng }
listing_broker_*              →        author/contact block
```

---

## 6. Phased execution plan

> Each phase ends in a **buildable, shippable** state. Recommend a feature branch
> per phase and small PRs.

### Phase 0 — Foundations & spike (0.5–1 day)
1. Create branch `feat/voyager-ui`.
2. Decide the design-token bridge: map Voyager's SCSS `__theme_colors` /
   `tailwind.config.js` palette into `app/globals.css` `@theme` (Tailwind v4).
   Convert any needed `.scss` to Tailwind utilities / CSS variables (no `sass`
   dependency in the target).
3. Add donor deps to `frontend/package.json` **only as needed**:
   `framer-motion`, `@headlessui/react` *(optional — prefer @base-ui/shadcn)*.
   Do **not** add `next-auth`, `sass`, `google-map-react` yet.
4. Spike: port **one** leaf atom (`ButtonPrimary` → existing `Button` variant)
   end-to-end to validate the Tailwind v4 + React 19 + alias workflow.

### Phase 1 — Design system & shared atoms (1–2 days)
- Port `src/shared/*` atoms into `components/ui/`, deduping against shadcn.
- Establish dark-mode toggle compatible with existing `@custom-variant dark`.
- Port Logo, Nav, header/footer shells. **No data changes.**
- Exit: Storybook-less visual check — header/footer render in current pages.

### Phase 2 — Landing / home (1–2 days)
- Re-skin `(landing)/page.tsx` sections (`Hero`, `FeaturedListings`,
  `CreProfessionals`, `ContactUs`) using Voyager hero + feature-grid layout.
- Wire `FeaturedListings` to real data via existing `listings`/`search` service
  through the §5 adapter.
- Exit: home page matches Voyager look, real listings render.

### Phase 3 — Listings index + search results (2–4 days) — *highest value*
- Port `SectionGridFilterCard`, `SectionGridHasMap`, `TabFilters`,
  `PropertyCardH` into `components/listings` + `components/search/result`.
- Replace `app/listings/page.tsx` ("coming soon") with the real grid.
- Wire `TabFilters` to `search` service `updateCriteria` + the
  `use-search-*` hooks. Map view: reuse existing Google Maps via
  `use-location`/`utils/listings/maps.ts` (do **not** introduce
  `google-map-react` unless the existing map proves insufficient).
- Adapt CRE fields on cards (size, clear height, docks, rent, broker).
- Exit: `/listings` and `/search/[id]` use Voyager UI on live results.

### Phase 4 — Listing detail (1–2 days)
- Port `(listing-detail)` layout + image gallery into `app/listings/[id]`.
- Drive with `use-listing-detail`; render CRE spec table + broker outreach CTA
  (links to existing `outreach` draft flow — no auto-send).
- Exit: detail page matches Voyager, real data + outreach draft intact.

### Phase 5 — Auth & account workspace (1–2 days)
- Re-skin `(auth)/sign-in` & `sign-up` with Voyager login look.
  **Keep Supabase forms, OAuth, `oauth-profile-sync`, `auth-session` untouched.**
- Re-skin `account` using Voyager "member workspace" layout + `config/brand.ts`
  dashboard copy, wired to existing `account` service sections.
- Exit: auth + account visually upgraded, all logic preserved.

### Phase 6 — Questionnaire / intake polish (1 day)
- Apply Voyager form/stepper styling to `questionnaire` + `search-wizard`
  context UI. Logic unchanged.

### Phase 7 — Cleanup & hardening (1 day)
- Remove `Voyager/` directory entirely (see §8).
- Drop unused deps; run `next build --webpack`, `eslint`, typecheck.
- Verify dark mode, responsive breakpoints, images `remotePatterns`
  (add Voyager's `images.pexels.com` / `a0.muscache.com` only if real assets use them).
- Update `README.md` / `docs/` screenshots.

**Rough total: ~10–16 working days** depending on how faithfully the Voyager
look must be reproduced and how many card/detail field variations exist.

---

## 7. Key technical gotchas

- **Tailwind v3 → v4:** Voyager's `tailwind.config.js` (colors, plugins
  `forms`/`typography`/`aspect-ratio`) must be re-expressed as v4 `@theme` tokens
  / `@plugin` imports in `globals.css`. Class names mostly carry over; arbitrary
  values and config-driven colors do not.
- **SCSS removal:** Convert the 6 `src/styles/*.scss` files (theme colors,
  date-picker, header) to CSS variables / Tailwind utilities. Avoid adding `sass`.
- **Next 13 → 16:** `params`/`searchParams` are now **async** (`await`); check
  `next/link`, `next/image` `legacyBehavior`, metadata API, and `typedRoutes`
  (`Route<string>` types from Voyager won't resolve — drop them).
- **Icons:** Replace `@heroicons/react` and `line-awesome` font icons with
  `lucide-react` (already a dependency) for consistency.
- **Auth collision:** Never run next-auth and Supabase together. Strip
  `Voyager/src/app/api/auth`, `SessionProvider`, `getServerSession` usages on port.
- **Domain mismatch:** Travel fields (guests/beds/reviews/saleOff) have **no CRE
  equivalent** — design the card to show CRE specs instead, not to fake reviews.
- **`react-hooks-global-state` / `react-use`:** prefer existing React 19 patterns
  and existing contexts; only port these if a component genuinely needs them.

---

## 8. Repo hygiene — handling the `Voyager/` folder

`Voyager/` is currently **untracked** and contains its own `.git/`,
`node_modules/`, `.next/`, `.vercel/`, and lockfiles (`yarn.lock`,
`package-lock.json`). It must **not** be committed as-is.

- Treat it as a **read-only reference** during porting (copy out of it).
- It is a nested git repo → either remove its `.git` if you want to track it
  temporarily, or (recommended) keep it out of version control and **delete it in
  Phase 7**.
- Add `Voyager/` to `.gitignore` while work is in progress so stray files from it
  never get staged.

---

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Scope creep porting 250 files | Port only what each phase's pages need; ignore travel/flight/car routes entirely |
| Visual fidelity vs. effort | Agree "close enough" bar with stakeholder per section before pixel-chasing |
| Regressions in working flows | Phase boundaries keep app buildable; manual smoke-test intake→search→outreach each phase |
| Tailwind v4 token drift | Lock the token bridge in Phase 0 before mass porting |
| Hidden next-auth coupling | Grep each ported file for `next-auth`, `signIn`, `useSession` before merge |

---

## 10. Immediate next steps

1. ~~Confirm Option A and scope~~ — **done** (see locked decisions at top:
   Option A, everything, light+dark, framer-motion).
2. Add `Voyager/` to `.gitignore`; create branch `feat/voyager-ui`.
3. Execute **Phase 0** spike: build the Tailwind v4 token bridge (incl. dark
   tokens), add `framer-motion`, and port one atom end-to-end to validate the
   workflow.
4. Proceed through **all** phases (1–7); since scope is "everything," every page
   group is in-scope before final cleanup. PR per phase.

---

## 11. Architecture & flow migration (ACTIVE PLAN — supersedes the reskin approach)

Decision (2026-06-06): adopt Voyager's **architecture, page composition, and user
flow**, wired to the existing data layer. This supersedes §6's section-by-section
reskin as the primary approach. Priority flows: Home/discovery, Listings+map,
Listing detail, Account workspace. Voyager's travel-only flows (flights, cars,
experiences) are skipped.

### 11.1 Architecture decisions
- **Routes:** keep Next `app/` routes (they own URLs + backend/auth coupling), but
  **rebuild each page as a composition of Voyager section components** instead of
  the existing ad-hoc sections.
- **Components:**
  - `components/ui/voyager/` — atoms (DONE: buttons, form controls, badge/tag/
    avatar, heading, pagination, nav, modal, dark-mode).
  - `components/voyager/` — Voyager's larger building blocks: property cards,
    image gallery, sliders, section blocks, hero search form, filter tabs, map.
  - Page-level sections colocated per route (Voyager style, e.g.
    `SectionGridFilterCard`) or under `components/voyager/sections/`.
- **Data layer (UNCHANGED):** `services/`, `hooks/`, `contexts/`, `lib/` stay the
  single source of truth. A thin **adapter** maps `SearchProperty` /
  `ListingDetailResponse` → the view-model that Voyager cards/detail expect
  (replaces Voyager's `data/*` demo + `StayDataType`).
- **Config:** add `config/brand.ts` (RadEstate brand/copy) mirroring Voyager's
  centralized config.
- **Types:** define a RadEstate **listing view-model** (e.g. `PropertyCardModel`)
  decoupled from Voyager's travel `StayDataType`.

### 11.2 Roadmap (phased; each phase shippable)
- **Phase A — Foundations:** `config/brand.ts`; listing view-model type +
  `SearchProperty → model` adapter; port core big components (PropertyCard,
  image gallery, specs row replacing StartRating, save/like → no-op or saved-list).
- **Phase B — Home/discovery:** Voyager home composition (SectionHero + search,
  category tabs, `SectionGridFeatureProperty`) wired to listings/search services.
- **Phase C — Listings + map:** `SectionGridFilterCard`, `TabFilters`,
  `SectionGridHasMap` (grid+map split) wired to the search service + existing
  maps util (`utils/listings/maps.ts`, `use-location`).
- **Phase D — Listing detail:** `(listing-detail)` layout (gallery, spec table,
  broker/outreach sidebar) wired to `use-listing-detail` + `outreach` (draft only).
- **Phase E — Account workspace:** `(account-pages)` layout (profile, collections,
  security) wired to the `account` service.
- **Phase F — Auth, questionnaire polish, cleanup, remove dead reskin code.**

### 11.3 Notes
- Earlier header/footer reskins stay; the home page (Phase B) may recompose the
  hero/featured sections into Voyager's section components.
- Keep the small-step + manual-commit + delete-`.tmp` workflow throughout.
