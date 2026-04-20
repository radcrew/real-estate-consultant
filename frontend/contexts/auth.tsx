"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";

import { getApiErrorMessage } from "@lib/api-errors";
import {
  AUTH_SESSION_CHANGED_EVENT,
  clearSession,
  readSession,
  saveSession,
  type StoredSession,
} from "@lib/auth-session";
import { OAUTH_CALLBACK_PATH } from "@lib/config";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";
import { authService } from "@services/auth";

export type AuthCredentials = {
  email: string;
  password: string;
};

export type AuthContextValue = {
  session: StoredSession | null;
  /** True after the client has read `sessionStorage` at least once (avoids a false signed-out flash). */
  ready: boolean;
  refresh: () => void;
  signOut: () => void;
  signIn: (credentials: AuthCredentials, onSuccess?: () => void) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signUp: (credentials: AuthCredentials, onSuccess?: () => void) => Promise<void>;
  error: string | null;
  isSubmitting: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type AuthProviderProps = {
  children: ReactNode;
};

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const pathname = usePathname();
  const [session, setSession] = useState<StoredSession | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  const refresh = useCallback(() => {
    setSession(readSession());
  }, []);

  useLayoutEffect(() => {
    refresh();
    setReady(true);
    setError(null);
  }, [pathname, refresh]);

  useEffect(() => {
    window.addEventListener(AUTH_SESSION_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, refresh);
  }, [refresh]);

  const signOut = useCallback(() => {
    clearSession();
  }, []);

  const signIn = useCallback(
    async ({ email, password }: AuthCredentials, onSuccess?: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        const {
          access_token: accessToken,
          refresh_token: refreshToken,
          expires_in: expiresIn,
          token_type: tokenType,
          user,
        } = await authService.signIn({
          email: email.trim(),
          password,
        });

        saveSession({
          accessToken,
          refreshToken,
          expiresIn,
          tokenType,
          user,
        });

        onSuccess?.();
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const signUp = useCallback(
    async ({ email, password }: AuthCredentials, onSuccess?: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        await authService.signUp({
          email: email.trim(),
          password,
        });

        onSuccess?.();
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const signInWithGoogle = useCallback(async () => {
    setError(null);
    setSubmitting(true);

    try {
      const supabase = getSupabaseBrowserClient();
      const { data, error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: { redirectTo: `${window.location.origin}${OAUTH_CALLBACK_PATH}` },
      });

      if (oauthError) {
        setError(oauthError.message);
        setSubmitting(false);
        return;
      }

      if (data.url) {
        window.location.assign(data.url);
        return;
      }

      setError("Could not start Google sign-in.");
      setSubmitting(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setSubmitting(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        ready,
        refresh,
        signOut,
        signIn,
        signInWithGoogle,
        signUp,
        error,
        isSubmitting,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
};
