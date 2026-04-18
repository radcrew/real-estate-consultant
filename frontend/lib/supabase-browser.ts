import { createClient, type SupabaseClient } from "@supabase/supabase-js";

import { SUPABASE_ANON_KEY, SUPABASE_URL } from "@lib/config";

let browserClient: SupabaseClient | undefined;

/**
 * Supabase client for the browser (e.g. OAuth). Call only from the client.
 * Set `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in `.env`.
 */
export const getSupabaseBrowserClient = (): SupabaseClient => {
  if (typeof window === "undefined") {
    throw new Error("getSupabaseBrowserClient() must only be called in the browser.");
  }

  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  }

  if (!browserClient) {
    browserClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }

  return browserClient;
};
