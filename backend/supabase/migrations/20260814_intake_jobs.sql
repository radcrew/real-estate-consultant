-- One row per LLM intake turn: the result store *and* the idempotency ledger.
--
-- Today the endpoint runs the turn inline, so a provider stall becomes a 5xx and the
-- user's typed answer is gone. A durable row makes the turn survivable and gives SQS
-- redelivery something to be idempotent against — at-least-once delivery makes that
-- mandatory rather than prudent, since a redelivered message would otherwise pay for a
-- second provider call for a result already in hand.
--
-- Rows are written *before* the SQS publish. A row with no message is visible and can be
-- redriven; a message with no row is undiagnosable when the consumer picks it up.

create table if not exists public.intake_jobs (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.intake_sessions (id) on delete cascade,
  status text not null default 'queued',
  -- The user's text, so a redrive can replay the turn rather than losing it.
  input text not null,
  -- The SubmitLlmIntakeInputResponse payload, handed to the client over SSE.
  result jsonb,
  error text,
  -- Counts queued -> running transitions, so a redelivery loop is visible here before
  -- the DLQ notices. Maintained by trigger; see below.
  attempts integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz,
  constraint intake_jobs_status_valid
    check (status in ('queued', 'running', 'succeeded', 'failed')),
  constraint intake_jobs_input_nonempty
    check (char_length(trim(input)) > 0)
);

-- Reads are always scoped by session (a job id alone must not read across sessions),
-- and the client polls its own job list newest-first.
create index if not exists intake_jobs_session_created_idx
  on public.intake_jobs (session_id, created_at desc);

-- Supports the per-session in-flight cap: one unfinished turn per session, which FIFO
-- ordering per MessageGroupId already implies.
create index if not exists intake_jobs_session_active_idx
  on public.intake_jobs (session_id)
  where status in ('queued', 'running');

comment on table public.intake_jobs is
  'One queued LLM intake turn. Result store and idempotency ledger for SQS redelivery.';
comment on column public.intake_jobs.attempts is
  'queued -> running transitions. Incremented by trigger, never by the worker.';

-- attempts must not be maintained by the consumer. PostgREST cannot express
-- "attempts = attempts + 1", and a read-then-write from the worker races concurrent
-- redelivery of the same message — two consumers would both read N and both write N+1.
-- Counting the transition server-side keeps it exact.
create or replace function public.intake_jobs_touch()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.status = 'running' and old.status = 'queued' then
    new.attempts := old.attempts + 1;
    new.started_at := now();
  end if;
  if new.status in ('succeeded', 'failed') and old.status not in ('succeeded', 'failed') then
    new.finished_at := now();
  end if;
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists intake_jobs_touch_trigger on public.intake_jobs;
create trigger intake_jobs_touch_trigger
  before update on public.intake_jobs
  for each row execute function public.intake_jobs_touch();

alter table public.intake_jobs enable row level security;

-- Backend data access uses the service role and bypasses RLS; this policy is
-- defense-in-depth if a user JWT is ever pointed at PostgREST directly. It mirrors the
-- visibility rule on intake_sessions, so a job is readable exactly when its session is.
--
-- Note this grants `authenticated` only, while intake itself is anonymous. That is why
-- clients follow a job through the API's SSE endpoint rather than Supabase Realtime,
-- which enforces RLS and would deliver nothing to an anonymous visitor. Widening this to
-- `anon` would let anyone holding a job id read the row directly, which is exactly what
-- scoping reads by session is meant to prevent.
-- No INSERT/UPDATE/DELETE for authenticated: only the API and the worker write here, and
-- a client that could flip status to 'succeeded' could forge a turn's result.
drop policy if exists "Users can read intake jobs for visible sessions" on public.intake_jobs;
create policy "Users can read intake jobs for visible sessions"
  on public.intake_jobs
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.intake_sessions s
      where s.id = intake_jobs.session_id
        and (
          s.search_profile_id is null
          or exists (
            select 1
            from public.search_profiles sp
            where sp.id = s.search_profile_id
              and sp.user_id = auth.uid()
          )
        )
    )
  );
