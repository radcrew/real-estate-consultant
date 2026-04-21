-- Allow authenticated API users to create/read/update intake sessions.
-- Endpoint access is already protected by backend auth.

alter table public.intake_sessions enable row level security;

create policy if not exists intake_sessions_select_authenticated
on public.intake_sessions
for select
to authenticated
using (true);

create policy if not exists intake_sessions_insert_authenticated
on public.intake_sessions
for insert
to authenticated
with check (true);

create policy if not exists intake_sessions_update_authenticated
on public.intake_sessions
for update
to authenticated
using (true)
with check (true);

notify pgrst, 'reload schema';
