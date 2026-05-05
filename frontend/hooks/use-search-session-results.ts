"use client";

import { useEffect, useState } from "react";

import { useSearchByProfile } from "@hooks/use-search-by-profile";
import { mapSearchPropertyMatchesToListings, type ResultCardListing } from "@lib/map-property-match";

const DEFAULT_PAGE = { limit: 20, offset: 0 } as const;

export const useSearchSessionResults = (sessionProfileId: string | undefined) => {
  const { search } = useSearchByProfile();
  const [listings, setListings] = useState<ResultCardListing[]>([]);
  const [criteria, setCriteria] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(() => Boolean(sessionProfileId?.trim()));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = sessionProfileId?.trim();
    if (!id) {
      setListings([]);
      setCriteria({});
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;

    setLoading(true);
    setError(null);
    setListings([]);
    setCriteria({});

    const run = async () => {
      try {
        const res = await search(id, { ...DEFAULT_PAGE });
        if (cancelled) {
          return;
        }
        setListings(mapSearchPropertyMatchesToListings(res.results));
        const c = res.criteria;
        setCriteria(
          c !== null && typeof c === "object" && !Array.isArray(c) ? { ...(c as Record<string, unknown>) } : {},
        );
      } catch {
        if (cancelled) {
          return;
        }
        setListings([]);
        setCriteria({});
        setError("Could not load search results. Try again later.");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [search, sessionProfileId]);

  return { listings, loading, error, criteria };
};
