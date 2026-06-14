-- Run in Supabase SQL Editor or via the Supabase CLI.
-- Enables live ingestion progress in the admin UI (Phase 3.5).

-- Allow admins to read job rows (required for Supabase Realtime, which
-- evaluates RLS using the subscriber's JWT).
alter table public.jobs enable row level security;

drop policy if exists "Admins can view jobs" on public.jobs;
create policy "Admins can view jobs"
  on public.jobs for select
  to authenticated
  using (
    exists (
      select 1
      from public.profiles
      where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
  );

-- Ensure UPDATE events carry the full new row (status, result, error, etc.)
-- so subscribers don't need a separate fetch to read changed columns.
alter table public.jobs replica identity full;

-- Stream INSERT/UPDATE/DELETE on this table to Realtime subscribers.
alter publication supabase_realtime add table public.jobs;
