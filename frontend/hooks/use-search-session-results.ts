"use client";

import { useCallback, useEffect, useState } from "react";

import { useSearchByProfile } from "@hooks/use-search-by-profile";
import { mapSearchPropertyMatchesToListings, type ResultCardListing } from "@lib/map-property-match";

const DEFAULT_PAGE = { limit: 20, offset: 0 } as const;

export const useSearchSessionResults = (sessionProfileId: string | undefined) => {
  const { search } = useSearchByProfile();
  const [listings, setListings] = useState<ResultCardListing[]>([]);
  const [criteria, setCriteria] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(() => Boolean(sessionProfileId?.trim()));
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (signal?: AbortSignal) => {
      const id = sessionProfileId?.trim();
      if (!id) {
        if (!signal?.aborted) {
          setListings([]);
          setCriteria({});
          setLoading(false);
          setError(null);
        }
        return;
      }

      if (!signal?.aborted) {
        setLoading(true);
        setError(null);
        setListings([]);
        setCriteria({});
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
        setCriteria({});
        setError("Could not load search results. Try again later.");
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [search, sessionProfileId],
  );

  useEffect(() => {
    const ac = new AbortController();
    void load(ac.signal);
    return () => ac.abort();
  }, [load]);

  const refetch = useCallback(() => {
    void load();
  }, [load]);

  return { listings, loading, error, criteria, refetch };
};
