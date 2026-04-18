export const BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_API_URL?.trim() || "http://localhost:8000";

export const SUPABASE_URL =
  process.env.NEXT_PUBLIC_SUPABASE_URL?.trim() ?? "";

export const SUPABASE_ANON_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() ?? "";

/** Supabase OAuth `redirectTo` path (must match app route + Supabase redirect allowlist). */
export const OAUTH_CALLBACK_PATH = "/auth/callback";
