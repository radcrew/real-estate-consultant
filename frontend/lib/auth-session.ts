const STORAGE_KEY = "radestate.session";

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
};

export const clearSession = (): void => {
  if (typeof window === "undefined") {
    return;
  }
  
  sessionStorage.removeItem(STORAGE_KEY);
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
