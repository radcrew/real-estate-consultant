-- intake_sessions had RLS enabled with zero policies, so any request using a
-- user JWT (instead of the service role) failed inserts with 42501.
-- Backend data access uses the service role (bypasses RLS); these policies are
-- defense-in-depth if a user JWT is ever used for PostgREST.

alter table public.intake_sessions enable row level security;

drop policy if exists "Authenticated users can insert intake sessions" on public.intake_sessions;
create policy "Authenticated users can insert intake sessions"
  on public.intake_sessions
  for insert
  to authenticated
  with check (true);

drop policy if exists "Users can read own intake sessions" on public.intake_sessions;
create policy "Users can read own intake sessions"
  on public.intake_sessions
  for select
  to authenticated
  using (
    search_profile_id is null
    or exists (
      select 1
      from public.search_profiles sp
      where sp.id = intake_sessions.search_profile_id
        and sp.user_id = auth.uid()
    )
  );

drop policy if exists "Users can update own intake sessions" on public.intake_sessions;
create policy "Users can update own intake sessions"
  on public.intake_sessions
  for update
  to authenticated
  using (
    search_profile_id is null
    or exists (
      select 1
      from public.search_profiles sp
      where sp.id = intake_sessions.search_profile_id
        and sp.user_id = auth.uid()
    )
  )
  with check (
    search_profile_id is null
    or exists (
      select 1
      from public.search_profiles sp
      where sp.id = intake_sessions.search_profile_id
        and sp.user_id = auth.uid()
    )
  );
