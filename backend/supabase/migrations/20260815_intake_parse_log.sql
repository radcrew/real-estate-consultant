-- Keep what users actually type at the intake model, so the eval can be grown from it.
--
-- Four production bugs were reported against a served adapter, and the 129-turn eval
-- could not have caught any of them: it was written before they were known, and nothing
-- persisted the turns that produced them. Reconstructing them meant asking the user what
-- they had typed. An eval that never sees production drifts into measuring the shapes it
-- already contains.
--
-- One row per intake parse. The columns are chosen so a row can become an eval turn by
-- adding gold: user_input and current_criteria are exactly a turn's inputs, and
-- model_output is what to triage against before labelling.
--
-- model_output is the schema-validated reply, not the raw text. The raw string lives
-- inside the provider and surfacing it would change generate_structured_output's
-- signature for fit, outreach and the opening question too. The cost is malformed-JSON
-- replies, which are already measured by the eval's raw_json_valid and were not the
-- failure class here -- all four bugs produced valid JSON that was simply wrong.

create table if not exists public.intake_parse_log (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references public.intake_sessions (id) on delete cascade,
  created_at timestamptz not null default now(),

  -- A turn's inputs. Together these reproduce the request exactly.
  user_input text not null,
  current_criteria jsonb not null default '{}'::jsonb,

  -- What the model said, and what the user ended up with after the filters. Keeping both
  -- is what makes a filter regression visible: they used to be the same object.
  model_output jsonb not null default '{}'::jsonb,
  extracted jsonb not null default '{}'::jsonb,
  unconfirmed_fields text[] not null default '{}'::text[],
  missing_fields text[] not null default '{}'::text[],

  -- Which model produced it. A row whose model is unknown cannot be attributed to an
  -- adapter, and comparing two adapters on production traffic is the point.
  model text,
  temperature real,
  latency_ms integer,

  constraint intake_parse_log_user_input_nonempty check (char_length(user_input) > 0)
);

-- Sampling is "the most recent N", and triage is "this session's turns in order".
create index if not exists intake_parse_log_created_at_idx
  on public.intake_parse_log (created_at desc);
create index if not exists intake_parse_log_session_idx
  on public.intake_parse_log (session_id, created_at);

comment on table public.intake_parse_log is
  'One row per intake extraction: the turn inputs, the model reply and the filtered '
  'result. Sampled to grow pipeline/eval/dataset.jsonl. Contains user free text.';
comment on column public.intake_parse_log.model_output is
  'Schema-validated model reply, before the criteria filters.';
comment on column public.intake_parse_log.extracted is
  'After the filters -- what the session actually stored.';
comment on column public.intake_parse_log.unconfirmed_fields is
  'Kept but unsupported by the message, so still asked about.';

-- This is internal telemetry holding user free text. The backend writes it with the
-- service role, which bypasses RLS; enabling RLS with no policy means a user JWT reaching
-- PostgREST can neither read nor write it, which is the intended answer for both.
alter table public.intake_parse_log enable row level security;
