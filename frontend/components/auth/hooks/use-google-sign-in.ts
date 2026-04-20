"use client";

import { useCallback, useState } from "react";

import { OAUTH_CALLBACK_PATH } from "@lib/config";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";

export const useGoogleSignIn = () => {
  const [error, setError] = useState<string | null>(null);
  const [isSigningIn, setSigningIn] = useState(false);

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    setSigningIn(true);

    try {
      const supabase = getSupabaseBrowserClient();
      const { data, error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}${OAUTH_CALLBACK_PATH}` },
      });

      if (oauthError) {
        setError(oauthError.message);
        setSigningIn(false);
        return;
      }

      if (data.url) {
        window.location.assign(data.url);
        return;
      }

      setError("Could not start Google sign-in.");
      setSigningIn(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSigningIn(false);
    }
  }, []);

  return { signInWithGoogle, error, isSigningIn };
};
