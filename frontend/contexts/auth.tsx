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
import { OAUTH_CALLBACK_PATH } from "@config/env";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";
import { authService } from "@services/auth";
import { accountService } from "@services/account";

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
  const avatarPatchedRef = useRef(false);

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

        // Fetch the profile in the background to populate avatarUrl in the
        // session — don't block sign-in if this fails.
        accountService.getProfile().then((profile) => {
          const stored = readSession();
          if (stored && profile.avatar_url) {
            saveSession({ ...stored, user: { ...stored.user, avatarUrl: profile.avatar_url } });
          }
        }).catch(() => {});

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

  // When a session is loaded without avatarUrl (e.g. after OAuth or a stale
  // cookie), fetch the profile once and patch it in so the avatar shows up.
  useEffect(() => {
    if (!session || session.user.avatarUrl != null || avatarPatchedRef.current) return;
    avatarPatchedRef.current = true;
    accountService.getProfile().then((profile) => {
      if (!profile.avatar_url) return;
      const stored = readSession();
      if (stored) {
        saveSession({ ...stored, user: { ...stored.user, avatarUrl: profile.avatar_url } });
      }
    }).catch(() => {});
  }, [session]);

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
