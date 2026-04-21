-- Store normalized search filters derived from intake criteria.

alter table public.search_profiles
    add column if not exists filters jsonb;

notify pgrst, 'reload schema';
