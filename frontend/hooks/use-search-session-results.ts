"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useSearchByProfile } from "@hooks/use-search-by-profile";
import { mapSearchPropertyMatchesToListings, type ResultCardListing } from "@utils/search/property";
import { buildDefaultSearchCriteriaShell } from "@utils/search/criteria";
import type { UpdateSearchCriteriaBody } from "@services/search";

const DEFAULT_PAGE = { limit: 20, offset: 0 } as const;

export const useSearchSessionResults = (sessionProfileId: string | undefined) => {
  const { search, updateCriteria } = useSearchByProfile();
  const [listings, setListings] = useState<ResultCardListing[]>([]);
  const [criteria, setCriteria] = useState<Record<string, unknown>>(() =>
    sessionProfileId?.trim() ? buildDefaultSearchCriteriaShell() : {},
  );
  const [loading, setLoading] = useState(() => Boolean(sessionProfileId?.trim()));
  const [error, setError] = useState<string | null>(null);
  const criteriaSessionRef = useRef<string | undefined>(undefined);

  const resetAll = () => {
    setListings([]);
    setCriteria({});
    setError(null);
    criteriaSessionRef.current = undefined;
  };

  const load = useCallback(
    async (signal?: AbortSignal) => {
      const id = sessionProfileId?.trim();
      if (!id) {
        if (!signal?.aborted) {
          setLoading(false);
          resetAll();
        }
        return;
      }

      if (!signal?.aborted) {
        setLoading(true);
        setError(null);
        setListings([]);
        if (criteriaSessionRef.current !== id) {
          criteriaSessionRef.current = id;
          setCriteria(buildDefaultSearchCriteriaShell());
        }
      }

      try {
        const res = await search(id, { ...DEFAULT_PAGE });
        if (signal?.aborted) {
          return;
        }

        setListings(mapSearchPropertyMatchesToListings(res.results));
        const c = res.criteria;
        setCriteria(
          c !== null && typeof c === "object" && !Array.isArray(c) ? { ...(c as Record<string, unknown>) } : {},
        );
      } catch {
        if (signal?.aborted) {
          return;
        }
        setListings([]);
        setError("Could not load search results. Try again later.");
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [search, sessionProfileId],
  );

  const applyCriteria = useCallback(
    async (nextCriteria: UpdateSearchCriteriaBody) => {
      const id = sessionProfileId?.trim();
      if (!id) {
        return;
      }
      setLoading(true);
      setError(null);
      try {
        await updateCriteria(id, nextCriteria);
        await load();
      } catch {
        setLoading(false);
        setError("Could not update criteria. Try again later.");
      }
    },
    [load, sessionProfileId, updateCriteria],
  );

  useEffect(() => {
    const abortController = new AbortController();
    load(abortController.signal);
    return () => abortController.abort();
  }, [load]);

  return { listings, loading, error, criteria, applyCriteria };
};
