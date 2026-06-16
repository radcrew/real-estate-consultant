"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@contexts/auth";
import { accountService } from "@services/account";

type SavedListingsContextValue = {
  savedIds: string[];
  isSaved: (id: string) => boolean;
  /** Toggle saved state. Redirects to sign-in when signed out. */
  toggle: (id: string) => void;
  /** Saved set has finished loading for the current auth state. */
  ready: boolean;
  signedIn: boolean;
};

const SavedListingsContext = createContext<SavedListingsContextValue>({
  savedIds: [],
  isSaved: () => false,
  toggle: () => {},
  ready: false,
  signedIn: false,
});

export const SavedListingsProvider = ({ children }: { children: ReactNode }) => {
  const { session, ready: authReady } = useAuth();
  const router = useRouter();
  const signedIn = Boolean(session);

  const [ids, setIds] = useState<Set<string>>(new Set());
  const [ready, setReady] = useState(false);
  const sessionAcRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!authReady) return;
    if (!session) {
      sessionAcRef.current = null;
      setIds(new Set());
      setReady(true);
      return;
    }

    const ac = new AbortController();
    sessionAcRef.current = ac;
    setReady(false);
    void (async () => {
      try {
        const list = await accountService.getSavedIds({ signal: ac.signal });
        if (!ac.signal.aborted) setIds(new Set(list));
      } catch {
        /* ignore — keep empty set */
      } finally {
        if (!ac.signal.aborted) setReady(true);
      }
    })();

    return () => {
      ac.abort();
      sessionAcRef.current = null;
    };
  }, [authReady, session]);

  const isSaved = useCallback((id: string) => ids.has(id), [ids]);

  const toggle = useCallback(
    (id: string) => {
      if (!session) {
        router.push("/sign-in");
        return;
      }
      const willSave = !ids.has(id);
      setIds((prev) => {
        const next = new Set(prev);
        if (willSave) next.add(id);
        else next.delete(id);
        return next;
      });
      const signal = sessionAcRef.current?.signal;
      const req = willSave
        ? accountService.addSaved(id, { signal })
        : accountService.removeSaved(id, { signal });
      req.catch(() => {
        if (!sessionAcRef.current || sessionAcRef.current.signal.aborted) return;
        // revert on failure
        setIds((prev) => {
          const next = new Set(prev);
          if (willSave) next.delete(id);
          else next.add(id);
          return next;
        });
      });
    },
    [session, router, ids],
  );

  return (
    <SavedListingsContext.Provider
      value={{ savedIds: [...ids], isSaved, toggle, ready, signedIn }}
    >
      {children}
    </SavedListingsContext.Provider>
  );
};

export const useSavedListings = () => useContext(SavedListingsContext);
