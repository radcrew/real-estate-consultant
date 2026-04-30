/** Pass criteria from the search wizard to `/search/results` without a backend round-trip. */

export const SEARCH_RESULTS_HANDOFF_KEY = "radestate.search-results.handoff";

export type SearchResultsChip = {
  label: string;
  value: string;
};

export type SearchResultsHandoff = {
  sessionId: string | null;
  chips: SearchResultsChip[];
};

let cachedHandoffRaw: string | null | undefined;
let cachedHandoffParsed: SearchResultsHandoff | null | undefined;

export const writeSearchResultsHandoff = (payload: SearchResultsHandoff): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(SEARCH_RESULTS_HANDOFF_KEY, JSON.stringify(payload));
  cachedHandoffRaw = undefined;
  cachedHandoffParsed = undefined;
};

/** Read handoff payload without removing it (safe for React Strict Mode and SSR). */
export const readSearchResultsHandoff = (): SearchResultsHandoff | null => {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = sessionStorage.getItem(SEARCH_RESULTS_HANDOFF_KEY);
  if (!raw) {
    return null;
  }
  try {
    const data = JSON.parse(raw) as SearchResultsHandoff;
    if (!data || !Array.isArray(data.chips)) {
      return null;
    }
    return data;
  } catch {
    return null;
  }
};

/**
 * Stable snapshot for ``useSyncExternalStore`` — returns the same object reference until
 * ``sessionStorage`` for this key changes (React requires cached getSnapshot results).
 */
export const getSearchResultsHandoffSnapshot = (): SearchResultsHandoff | null => {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = sessionStorage.getItem(SEARCH_RESULTS_HANDOFF_KEY);
  if (raw === cachedHandoffRaw) {
    return cachedHandoffParsed ?? null;
  }
  cachedHandoffRaw = raw;
  if (!raw) {
    cachedHandoffParsed = null;
    return null;
  }
  try {
    const data = JSON.parse(raw) as SearchResultsHandoff;
    if (!data || !Array.isArray(data.chips)) {
      cachedHandoffParsed = null;
      return null;
    }
    cachedHandoffParsed = data;
    return data;
  } catch {
    cachedHandoffParsed = null;
    return null;
  }
};

export const clearSearchResultsHandoff = (): void => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(SEARCH_RESULTS_HANDOFF_KEY);
  cachedHandoffRaw = undefined;
  cachedHandoffParsed = undefined;
};
