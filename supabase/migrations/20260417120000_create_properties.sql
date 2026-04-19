-- Normalized commercial listings (seeded from backend dataset).
-- Apply with Supabase CLI (`supabase db push`) or paste into SQL Editor.

create table if not exists public.properties (
    id uuid primary key default gen_random_uuid(),
    address text,
    city text,
    state text,
    country text,
    latitude double precision,
    longitude double precision,
    property_type text,
    listing_type text,
    size_sqft numeric,
    price numeric,
    rent numeric,
    clear_height numeric,
    loading_docks integer,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists properties_city_state_idx on public.properties (city, state);

create or replace function public.properties_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists properties_set_updated_at on public.properties;
create trigger properties_set_updated_at
before update on public.properties
for each row
execute function public.properties_set_updated_at();

alter table public.properties enable row level security;

-- Adjust policies for your app; service role bypasses RLS for server-side seeding.

notify pgrst, 'reload schema';
