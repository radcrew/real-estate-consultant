-- MCP API keys: long-lived credentials bound to auth.users for agent hosts.
-- Backend resolves raw key → user_id; only key_hash is stored (never plaintext).
-- Design freeze: see MCP_AUTH_PLAN.md (Phase 0).

create table if not exists public.mcp_api_keys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null default 'default',
  key_prefix text not null,
  key_hash text not null,
  scopes text[] not null default array['*']::text[],
  created_at timestamptz not null default now(),
  last_used_at timestamptz,
  revoked_at timestamptz,
  expires_at timestamptz,
  constraint mcp_api_keys_key_hash_unique unique (key_hash),
  constraint mcp_api_keys_prefix_format check (char_length(key_prefix) >= 8),
  constraint mcp_api_keys_name_nonempty check (char_length(trim(name)) > 0)
);

create index if not exists mcp_api_keys_user_id_idx
  on public.mcp_api_keys (user_id);

-- Lookup candidates by public prefix before hash verify.
create index if not exists mcp_api_keys_prefix_active_idx
  on public.mcp_api_keys (key_prefix)
  where revoked_at is null;

comment on table public.mcp_api_keys is
  'Hashed MCP API keys; plaintext shown once at creation. Prefix rad_.';

comment on column public.mcp_api_keys.key_prefix is
  'First characters of the key (including rad_) for indexed candidate lookup.';

comment on column public.mcp_api_keys.key_hash is
  'sha256 hex of (pepper || raw_key). Not protected by RLS alone — see column grants.';

comment on column public.mcp_api_keys.scopes is
  'Optional scopes for later gating; v1 uses {*} full access.';

alter table public.mcp_api_keys enable row level security;

-- Row ownership only. RLS does not hide columns: authenticated users can still
-- SELECT key_hash on their own rows unless column privileges revoke it
-- (see 20260728_mcp_api_keys_hide_key_hash.sql). API responses omit key_hash.
drop policy if exists "Users can select own mcp api keys" on public.mcp_api_keys;
create policy "Users can select own mcp api keys"
  on public.mcp_api_keys
  for select
  to authenticated
  using (auth.uid() = user_id);

-- No INSERT/UPDATE/DELETE for authenticated: browser PostgREST must not
-- create keys, un-revoke, change scopes/expiry, or delete rows. Mutations are
-- service_role only (FastAPI account/api-keys + auth resolve). See
-- 20260729_mcp_api_keys_lock_mutations.sql for deploys that already applied
-- the older write policies.
