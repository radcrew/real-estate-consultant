const STORAGE_KEY = "radestate.session";

/** Dispatched on the window after `saveSession` / `clearSession` so clients can re-sync UI. */
export const AUTH_SESSION_CHANGED_EVENT = "radestate:auth-session-changed";

const emitSessionChange = (): void => {
  if (typeof window === "undefined") {
    return;
  }
  window.dispatchEvent(new Event(AUTH_SESSION_CHANGED_EVENT));
};

export type StoredSession = {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
  user: { id: string; email: string | null };
};

export const saveSession = (session: StoredSession): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  emitSessionChange();
};

export const clearSession = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  sessionStorage.removeItem(STORAGE_KEY);
  emitSessionChange();
};

export const readSession = (): StoredSession | null => {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
};
