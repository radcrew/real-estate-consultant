-- Users now come from AWS Cognito, not Supabase Auth.
--
-- Tables stay keyed by a uuid. For users moved over from Supabase Auth it is their old
-- auth.users id, found through public.cognito_identity_mapping. A user with no mapping row
-- (anyone who signed up through Cognito) uses their Cognito `sub` as the id, and that id
-- never exists in auth.users. Any foreign key into auth.users would reject every row such
-- a user writes, so drop them all, except the one on cognito_identity_mapping.uuid: that
-- column only ever holds real auth.users ids, and the key keeps the mapping honest.
--
-- The loop also catches keys created outside this folder (profiles, saved_listings,
-- search_profiles, outreach_drafts, favorites were never defined here).
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
      and con.conrelid <> 'public.cognito_identity_mapping'::regclass
  loop
    execute format('alter table %s drop constraint %I', fk.table_name, fk.conname);
  end loop;
end
$$;

-- Phone was stored on the Supabase auth user. It is profile data now.
alter table public.profiles
  add column if not exists phone text;
