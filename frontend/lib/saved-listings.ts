/**
 * Client-side persistence for "saved" (liked) listings, backed by localStorage.
 * A lightweight stand-in until a saved-listings backend exists.
 */
const STORAGE_KEY = "radestate:saved-listings";

const read = (): Set<string> => {
  if (typeof window === "undefined") {
    return new Set();
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === "string") : []);
  } catch {
    return new Set();
  }
};

const write = (ids: Set<string>): void => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
  } catch {
    /* storage unavailable / quota — ignore */
  }
};

export const isSavedListing = (id: string): boolean => read().has(id);

/** Toggle a listing's saved state; returns the new saved value. */
export const toggleSavedListing = (id: string): boolean => {
  const ids = read();
  const nowSaved = !ids.has(id);
  if (nowSaved) {
    ids.add(id);
  } else {
    ids.delete(id);
  }
  write(ids);
  return nowSaved;
};
