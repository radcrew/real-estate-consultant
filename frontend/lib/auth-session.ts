const STORAGE_KEY = "radestate.session";
const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

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
  user: {
    id: string;
    email: string | null;
    avatarUrl?: string | null;
  };
};

const writeSessionCookie = (session: StoredSession): void => {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie = `${STORAGE_KEY}=${encodeURIComponent(JSON.stringify(session))}; Path=/; Max-Age=${COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;
};

const clearSessionCookie = (): void => {
  if (typeof document === "undefined") {
    return;
  }

  document.cookie = `${STORAGE_KEY}=; Path=/; Max-Age=0; SameSite=Lax`;
};

const readSessionFromCookie = (): StoredSession | null => {
  if (typeof document === "undefined") {
    return null;
  }

  const prefix = `${STORAGE_KEY}=`;
  const cookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(prefix));

  if (!cookie) {
    return null;
  }

  try {
    return JSON.parse(decodeURIComponent(cookie.slice(prefix.length))) as StoredSession;
  } catch {
    return null;
  }
};

export const saveSession = (session: StoredSession): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  writeSessionCookie(session);
  emitSessionChange();
};

export const clearSession = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  sessionStorage.removeItem(STORAGE_KEY);
  clearSessionCookie();
  emitSessionChange();
};

export const readSession = (): StoredSession | null => {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    const fromCookie = readSessionFromCookie();
    if (fromCookie) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(fromCookie));
      return fromCookie;
    }
    return null;
  }

  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
};
