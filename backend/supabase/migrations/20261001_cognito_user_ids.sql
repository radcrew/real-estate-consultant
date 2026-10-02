-- Users now come from AWS Cognito, not Supabase Auth.
--
-- Every user_id / profiles.id column keeps its uuid type and from now on holds the
-- Cognito `sub`. Those users never exist in auth.users, so any foreign key into it would
-- reject every new row. Drop them all. Known ones: mcp_api_keys.user_id and
-- intake_sessions.user_id; the loop also catches keys created outside this folder
-- (saved_listings, search_profiles, outreach_drafts were never defined here).
--
-- ⚠️ Existing rows keep their Supabase user ids and match no Cognito user. That is the
-- agreed cut-over: old accounts are not migrated.
--
-- RLS policies that compare against auth.uid() are left in place. The backend uses the
-- service role and bypasses them, and the browser no longer queries these tables with a
-- Supabase session, so they match nothing.

do $$
declare
  fk record;
begin
  for fk in
    select con.conrelid::regclass as table_name, con.conname
    from pg_constraint con
    join pg_namespace ns on ns.oid = con.connamespace
    where con.contype = 'f'
      and con.confrelid = 'auth.users'::regclass
      and ns.nspname = 'public'
  loop
    execute format('alter table %s drop constraint %I', fk.table_name, fk.conname);
  end loop;
end
$$;

-- Phone was stored on the Supabase auth user. It is profile data now.
alter table public.profiles
  add column if not exists phone text;
