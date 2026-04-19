"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
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

  const refresh = useCallback(() => {
    setSession(readSession());
  }, []);

  useEffect(() => {
    refresh();
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
      refresh,
      signOut,
    }),
    [session, refresh, signOut],
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
