-- Questionnaire question definitions (MVP flow).

create table if not exists public.questions (
    id uuid not null default gen_random_uuid(),
    text text not null,
    type text not null default 'text',
    order_index integer not null,
    created_at timestamptz not null default now(),
    required boolean not null default false,
    options jsonb,
    key text not null,
    constraint questions_pkey primary key (id)
);

create index if not exists questions_order_index_idx on public.questions (order_index);

alter table public.questions enable row level security;

notify pgrst, 'reload schema';
