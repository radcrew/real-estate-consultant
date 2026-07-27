-- key_hash must not be readable via PostgREST user JWTs.
-- RLS only filters rows; without column privileges, SELECT * still returns key_hash
-- for the caller's own rows. Impact is low (pepper + 256-bit body), but we enforce
-- the intended boundary: hashes are service-role only.
-- service_role bypasses RLS and keeps full access as table owner / privileged role.

comment on column public.mcp_api_keys.key_hash is
  'sha256 hex of (pepper || raw_key). Readable by service_role only; revoked from authenticated/anon.';

-- Convert table-level SELECT/UPDATE into column privileges that omit key_hash.
revoke select (key_hash) on table public.mcp_api_keys from authenticated;
revoke select (key_hash) on table public.mcp_api_keys from anon;
revoke update (key_hash) on table public.mcp_api_keys from authenticated;
revoke update (key_hash) on table public.mcp_api_keys from anon;
