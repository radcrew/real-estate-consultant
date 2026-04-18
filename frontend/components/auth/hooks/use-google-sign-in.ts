"use client";

import { useCallback, useState } from "react";

import { OAUTH_CALLBACK_PATH } from "@lib/config";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";

export const useGoogleSignIn = () => {
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    setPending(true);

    try {
      const supabase = getSupabaseBrowserClient();
      const { data, error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}${OAUTH_CALLBACK_PATH}` },
      });

      if (oauthError) {
        setError(oauthError.message);
        setPending(false);
        return;
      }

      if (data.url) {
        window.location.assign(data.url);
        return;
      }

      setError("Could not start Google sign-in.");
      setPending(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setPending(false);
    }
  }, []);

  return { signInWithGoogle, error, pending };
};
