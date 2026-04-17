-- If `public.properties` already existed when the first migration ran, `CREATE TABLE IF NOT EXISTS`
-- did nothing and columns may be missing. This migration adds any missing seed columns.

alter table public.properties add column if not exists address text;
alter table public.properties add column if not exists city text;
alter table public.properties add column if not exists state text;
alter table public.properties add column if not exists country text;
alter table public.properties add column if not exists latitude double precision;
alter table public.properties add column if not exists longitude double precision;
alter table public.properties add column if not exists property_type text;
alter table public.properties add column if not exists listing_type text;
alter table public.properties add column if not exists size_sqft numeric;
alter table public.properties add column if not exists price numeric;
alter table public.properties add column if not exists rent numeric;
alter table public.properties add column if not exists clear_height numeric;
alter table public.properties add column if not exists loading_docks integer;
alter table public.properties add column if not exists created_at timestamptz not null default now();
alter table public.properties add column if not exists updated_at timestamptz not null default now();

notify pgrst, 'reload schema';
