"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";

import { getApiErrorMessage } from "@utils/common";
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

export type SignUpCredentials = {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
};

export type AuthContextValue = {
  session: StoredSession | null;
  ready: boolean;
  refresh: () => void;
  signOut: () => void;
  signIn: (credentials: AuthCredentials, onSuccess: () => void) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signUp: (credentials: SignUpCredentials, onSuccess: () => void) => Promise<void>;
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
  const googleOAuthInFlightRef = useRef(false);

  const signIn = useCallback(
    async ({ email, password }: AuthCredentials, onSuccess: () => void) => {
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

        onSuccess();
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const startGoogleOAuth = useCallback(async () => {
    if (googleOAuthInFlightRef.current) {
      return;
    }

    googleOAuthInFlightRef.current = true;
    setError(null);
    setSubmitting(true);

    try {
      const supabase = getSupabaseBrowserClient();
      const { data, error: oauthError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}${OAUTH_CALLBACK_PATH}`,
        },
      });

      if (oauthError) {
        console.error("[auth] Google sign-in failed:", oauthError.message);
        setError("Could not start Google sign-in. Please try again.");
        setSubmitting(false);
        googleOAuthInFlightRef.current = false;
        return;
      }

      if (data.url) {
        window.location.assign(data.url);
        return;
      }

      setError("Could not start Google sign-in. Please try again.");
      setSubmitting(false);
      googleOAuthInFlightRef.current = false;
    } catch (err) {
      console.error("[auth] Google sign-in failed:", err);
      setError("Could not start Google sign-in. Please try again.");
      setSubmitting(false);
      googleOAuthInFlightRef.current = false;
    }
  }, []);

  const signUp = useCallback(
    async ({ email, password, firstName, lastName }: SignUpCredentials, onSuccess: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        await authService.signUp({
          email: email.trim(),
          password,
          first_name: firstName,
          last_name: lastName,
        });

        onSuccess();
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const signInWithGoogle = useCallback(() => startGoogleOAuth(), [startGoogleOAuth]);

  const signOut = useCallback(() => {
    clearSession();
  }, []);

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

  return (
    <AuthContext.Provider
      value={{
        session,
        ready,
        signIn,
        signInWithGoogle,
        signUp,
        signOut,
        refresh,
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
