alter table public.properties add column if not exists description text;

notify pgrst, 'reload schema';
