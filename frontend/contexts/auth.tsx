"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";

import {
  AUTH_SESSION_CHANGED_EVENT,
  clearSession,
  readSession,
  type StoredSession,
} from "@lib/auth-session";

export type AuthContextValue = {
  session: StoredSession | null;
  /** True after the client has read `sessionStorage` at least once (avoids a false signed-out flash). */
  ready: boolean;
  refresh: () => void;
  signOut: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

type AuthProviderProps = {
  children: ReactNode;
};

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const pathname = usePathname();
  const [session, setSession] = useState<StoredSession | null>(null);
  const [ready, setReady] = useState(false);

  const refresh = useCallback(() => {
    setSession(readSession());
  }, []);

  useLayoutEffect(() => {
    refresh();
    setReady(true);
  }, [pathname, refresh]);

  useEffect(() => {
    window.addEventListener(AUTH_SESSION_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, refresh);
  }, [refresh]);

  const signOut = useCallback(() => {
    clearSession();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      ready,
      refresh,
      signOut,
    }),
    [session, ready, refresh, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
};
