-- Run in Supabase SQL Editor or via the Supabase CLI.
-- Creates the async ingestion job queue (Phase 3.3).

create table if not exists public.jobs (
  id               uuid         primary key default gen_random_uuid(),
  source           text         not null,
  status           text         not null default 'pending'
                                check (status in ('pending', 'running', 'done', 'failed')),
  attempts         int          not null default 0,
  idempotency_key  text         not null,
  result           jsonb,
  error            text,
  created_at       timestamptz  not null default now(),
  updated_at       timestamptz  not null default now()
);

-- One active job per idempotency key at a time (prevents duplicate runs).
create unique index if not exists jobs_active_idempotency_key_idx
  on public.jobs (idempotency_key)
  where status in ('pending', 'running');

-- Fast pending-job lookups ordered by arrival time.
create index if not exists jobs_pending_created_at_idx
  on public.jobs (created_at)
  where status = 'pending';

-- Auto-update updated_at on every row change.
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists jobs_set_updated_at on public.jobs;
create trigger jobs_set_updated_at
  before update on public.jobs
  for each row execute function public.set_updated_at();

-- Atomically claims one pending job.
-- FOR UPDATE SKIP LOCKED prevents two concurrent workers from claiming the same row.
create or replace function public.claim_next_job()
returns setof public.jobs
language sql as $$
  update public.jobs
  set    status     = 'running',
         attempts   = attempts + 1,
         updated_at = now()
  where  id = (
    select id
    from   public.jobs
    where  status = 'pending'
    order  by created_at
    limit  1
    for    update skip locked
  )
  returning *;
$$;
