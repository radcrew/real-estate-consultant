-- Give intake sessions an owner.
--
-- The endpoints have always required authentication, but the row recorded no user, so
-- any authenticated caller holding a session UUID could read or continue anyone else's
-- intake conversation — and those hold budget, location and personal circumstances. The
-- session id was effectively a bearer token that nothing re-checked.
--
-- ⚠️ Existing rows get a NULL owner and become inaccessible. That is the deliberate
-- direction: an unowned session cannot be matched to a caller, and guessing an owner
-- would hand someone else's conversation to whoever asked first. Intake sessions are
-- short-lived, so the blast radius is conversations in flight at deploy time, which
-- restart cleanly. Deploy this at a quiet moment if that matters.

alter table public.intake_sessions
  add column if not exists user_id uuid references auth.users (id) on delete cascade;

create index if not exists intake_sessions_user_id_idx
  on public.intake_sessions (user_id);

comment on column public.intake_sessions.user_id is
  'Owner. NULL only for rows created before ownership existed; those are unreachable.';

-- The previous policies allowed any authenticated user to read or update a session whose
-- search_profile_id was null — which is every session before it is completed, i.e. every
-- session during the conversation the policy was meant to protect.
drop policy if exists "Users can read own intake sessions" on public.intake_sessions;
create policy "Users can read own intake sessions"
  on public.intake_sessions
  for select
  to authenticated
  using (user_id = auth.uid());

drop policy if exists "Users can update own intake sessions" on public.intake_sessions;
create policy "Users can update own intake sessions"
  on public.intake_sessions
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- Inserts still come from the backend under the service role; requiring the row to claim
-- the inserting user keeps a JWT-authenticated client from creating a session it does not
-- own if one is ever pointed at PostgREST.
drop policy if exists "Authenticated users can insert intake sessions" on public.intake_sessions;
create policy "Authenticated users can insert intake sessions"
  on public.intake_sessions
  for insert
  to authenticated
  with check (user_id = auth.uid());

-- Jobs inherit the session's owner. The previous policy granted select to every
-- authenticated user for any session with no search profile, which is the same hole.
drop policy if exists "Users can read intake jobs for visible sessions" on public.intake_jobs;
create policy "Users can read intake jobs for own sessions"
  on public.intake_jobs
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.intake_sessions s
      where s.id = intake_jobs.session_id
        and s.user_id = auth.uid()
    )
  );
