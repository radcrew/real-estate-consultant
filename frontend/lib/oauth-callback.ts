import { saveSession } from "@lib/auth-session";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";

/**
 * Reads Supabase session after OAuth redirect, persists app session, then runs callbacks.
 * Call only from the client (e.g. auth callback route).
 */
export const handleOAuthCallback = async (
  onAuthenticated: () => void,
  onAuthFailed: (message: string) => void,
  isCancelled: () => boolean,
  setHint: (message: string) => void,
): Promise<void> => {
  try {
    const supabase = getSupabaseBrowserClient();
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();

    if (isCancelled()) {
      return;
    }

    if (error) {
      onAuthFailed(error.message);
      return;
    }

    if (!session?.refresh_token) {
      onAuthFailed("No session returned. Try signing in again.");
      return;
    }

    saveSession({
      accessToken: session.access_token,
      refreshToken: session.refresh_token,
      expiresIn: session.expires_in ?? 3600,
      tokenType: session.token_type,
      user: {
        id: session.user.id,
        email: session.user.email ?? null,
      },
    });
    onAuthenticated();
  } catch (err) {
    if (isCancelled()) {
      return;
    }

    const message = err instanceof Error ? err.message : "Sign-in failed.";
    setHint(message);
    onAuthFailed(message);
  }
};
