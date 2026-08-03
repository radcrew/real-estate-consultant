/** Backend origin without trailing slash (avoids `//api/v1` URLs that break CORS preflight). */
export const BACKEND_BASE_URL = (
  process.env.NEXT_PUBLIC_BACKEND_API_URL?.trim() || "http://localhost:8888"
).replace(/\/+$/, "");

/**
 * Streamable-HTTP endpoint of the MCP adapter, used to build client config
 * snippets. Defaults to the local `pnpm run dev:mcp` bind; set this to the
 * deployed URL in preview/production.
 */
export const MCP_SERVER_URL = (
  process.env.NEXT_PUBLIC_MCP_URL?.trim() || "http://127.0.0.1:8900/mcp"
).replace(/\/+$/, "");

export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? "";

export const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? "";

export const GOOGLE_MAPS_API_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY?.trim() ?? "";

// Web3Forms access key for the contact form (https://web3forms.com).
export const WEB3FORMS_ACCESS_KEY =
  process.env.NEXT_PUBLIC_WEB3FORMS_ACCESS_KEY?.trim() ?? "";

export const OAUTH_CALLBACK_PATH = "/auth/callback";
