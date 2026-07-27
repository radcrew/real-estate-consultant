-- Authenticated browser clients (frontend Supabase JWT → PostgREST) must not
-- mutate mcp_api_keys. The open UPDATE policy allowed row owners to:
--   update mcp_api_keys set revoked_at = null, expires_at = null, scopes = '{*}'
-- Create / revoke / touch last_used_at go through the backend (service_role).
-- Keep SELECT of own metadata (key_hash still column-revoked).

drop policy if exists "Users can update own mcp api keys" on public.mcp_api_keys;
drop policy if exists "Users can insert own mcp api keys" on public.mcp_api_keys;
drop policy if exists "Users can delete own mcp api keys" on public.mcp_api_keys;

revoke insert, update, delete on table public.mcp_api_keys from authenticated;
revoke insert, update, delete on table public.mcp_api_keys from anon;
