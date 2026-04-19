-- Intake session state (linked to a saved search profile).

create table if not exists public.intake_sessions (
    id uuid not null default gen_random_uuid(),
    status text not null default 'in_progress',
    created_at timestamptz not null default now(),
    search_profile_id uuid default gen_random_uuid() references public.search_profiles (id),
    criteria jsonb,
    constraint intake_sessions_pkey primary key (id)
);

create index if not exists intake_sessions_search_profile_id_idx
    on public.intake_sessions (search_profile_id);

alter table public.intake_sessions enable row level security;

notify pgrst, 'reload schema';
