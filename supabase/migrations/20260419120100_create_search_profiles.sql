-- User-owned saved search profiles.

create table if not exists public.search_profiles (
    id uuid not null default gen_random_uuid(),
    user_id uuid references auth.users (id),
    name text,
    created_at timestamp without time zone default now(),
    constraint search_profiles_pkey primary key (id)
);

create index if not exists search_profiles_user_id_idx on public.search_profiles (user_id);

alter table public.search_profiles enable row level security;

notify pgrst, 'reload schema';
