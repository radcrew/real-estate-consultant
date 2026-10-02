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
import { isAxiosError } from "axios";
import { usePathname } from "next/navigation";

import { getApiErrorMessage } from "@utils/common";
import {
  AUTH_SESSION_CHANGED_EVENT,
  clearSession,
  readSession,
  saveSession,
  toStoredSession,
  type StoredSession,
} from "@lib/auth-session";
import { OAUTH_START_PATH } from "@config/env";
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

export type SignUpResult = {
  // True when Cognito emailed a code that must be confirmed before sign-in.
  confirmationRequired: boolean;
};

export type AuthContextValue = {
  session: StoredSession | null;
  ready: boolean;
  refresh: () => void;
  signOut: () => void;
  signIn: (
    credentials: AuthCredentials,
    onSuccess: () => void,
    onUnconfirmed?: () => void,
  ) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signUp: (
    credentials: SignUpCredentials,
    onSuccess: (result: SignUpResult) => void,
  ) => Promise<void>;
  confirmSignUp: (email: string, code: string, onSuccess: () => void) => Promise<void>;
  resendCode: (email: string, onSuccess: () => void) => Promise<void>;
  requestPasswordReset: (email: string, onSuccess: () => void) => Promise<void>;
  updatePassword: (password: string, onSuccess: () => void) => Promise<void>;
  clearError: () => void;
  error: string | null;
  isSubmitting: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

// The backend's 403 detail for a sign-in by an account whose email is not confirmed yet.
const EMAIL_NOT_CONFIRMED_DETAIL = "Confirm your email address before signing in.";

const isEmailNotConfirmed = (err: unknown): boolean =>
  isAxiosError(err) &&
  err.response?.status === 403 &&
  (err.response.data as { detail?: unknown } | undefined)?.detail === EMAIL_NOT_CONFIRMED_DETAIL;

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
    async (
      { email, password }: AuthCredentials,
      onSuccess: () => void,
      onUnconfirmed?: () => void,
    ) => {
      setError(null);
      setSubmitting(true);

      try {
        const data = await authService.signIn({
          email: email.trim(),
          password,
        });

        saveSession(toStoredSession(data));

        // Fetch the profile in the background to populate avatarUrl in the
        // session — don't block sign-in if this fails.
        accountService.getProfile().then((profile) => {
          const stored = readSession();
          if (stored && profile.avatar_url) {
            saveSession({ ...stored, user: { ...stored.user, avatarUrl: profile.avatar_url } });
          }
        }).catch((err) => {
          console.warn("[auth] background profile fetch failed:", err);
        });

        onSuccess();
      } catch (err) {
        if (onUnconfirmed && isEmailNotConfirmed(err)) {
          onUnconfirmed();
          return;
        }
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

    // The route handler sets the state cookie and redirects to Cognito's Hosted UI.
    const next = new URLSearchParams(window.location.search).get("next");
    const target = next
      ? `${OAUTH_START_PATH}?next=${encodeURIComponent(next)}`
      : OAUTH_START_PATH;
    window.location.assign(target);
  }, []);

  const signUp = useCallback(
    async (
      { email, password, firstName, lastName }: SignUpCredentials,
      onSuccess: (result: SignUpResult) => void,
    ) => {
      setError(null);
      setSubmitting(true);

      try {
        const data = await authService.signUp({
          email: email.trim(),
          password,
          first_name: firstName,
          last_name: lastName,
        });

        onSuccess({ confirmationRequired: data.confirmation_required });
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const confirmSignUp = useCallback(
    async (email: string, code: string, onSuccess: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        await authService.confirmSignUp(email.trim(), code.trim());
        onSuccess();
      } catch (err) {
        setError(getApiErrorMessage(err));
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const resendCode = useCallback(async (email: string, onSuccess: () => void) => {
    setError(null);
    setSubmitting(true);

    try {
      await authService.resendCode(email.trim());
      onSuccess();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }, []);

  const requestPasswordReset = useCallback(
    async (email: string, onSuccess: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        const supabase = getSupabaseBrowserClient();
        const { error: resetError } = await supabase.auth.resetPasswordForEmail(
          email.trim(),
          { redirectTo: `${window.location.origin}/reset-password` },
        );

        if (resetError) {
          console.error("[auth] password reset request failed:", resetError.message);
          setError("Could not send the reset email. Please try again.");
          return;
        }

        onSuccess();
      } catch (err) {
        console.error("[auth] password reset request failed:", err);
        setError("Could not send the reset email. Please try again.");
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const updatePassword = useCallback(
    async (password: string, onSuccess: () => void) => {
      setError(null);
      setSubmitting(true);

      try {
        const supabase = getSupabaseBrowserClient();
        const { error: updateError } = await supabase.auth.updateUser({ password });

        if (updateError) {
          setError(
            updateError.message ||
              "Could not update your password. Your reset link may have expired.",
          );
          return;
        }

        onSuccess();
      } catch (err) {
        console.error("[auth] password update failed:", err);
        setError("Could not update your password. Please try again.");
      } finally {
        setSubmitting(false);
      }
    },
    [],
  );

  const clearError = useCallback(() => setError(null), []);

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
    }).catch((err) => {
      console.warn("[auth] background avatar fetch failed:", err);
    });
  }, [session]);

  return (
    <AuthContext.Provider
      value={{
        session,
        ready,
        signIn,
        signInWithGoogle,
        signUp,
        confirmSignUp,
        resendCode,
        requestPasswordReset,
        updatePassword,
        clearError,
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
