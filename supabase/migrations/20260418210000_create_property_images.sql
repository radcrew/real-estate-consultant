-- Gallery URLs per property (seeded from dataset ``KVImages``).

create table if not exists public.property_images (
    id uuid primary key default gen_random_uuid(),
    property_id uuid not null references public.properties (id) on delete cascade,
    url text not null,
    created_at timestamptz not null default now()
);

create index if not exists property_images_property_id_idx
    on public.property_images (property_id);

alter table public.property_images enable row level security;

notify pgrst, 'reload schema';
