"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  toPropertyModels,
  type PropertyModel,
} from "@components/property/listing-model";
import { searchService, type UpdateSearchCriteriaBody } from "@services/search";
import { buildDefaultSearchCriteriaShell } from "@utils/search/criteria";

/**
 * Property search-results hook.
 *
 * Loads results on session change (with abort handling, a default criteria
 * shell, and `applyCriteria`) and maps the raw `SearchPropertyMatch[]` to the
 * richer `PropertyModel[]` (via `toPropertyModels`) so the grid AND map (which
 * needs lat/lng) share one source.
 */
const DEFAULT_PAGE = { limit: 20, offset: 0 } as const;

export const useSearchResults = (
  sessionProfileId: string | undefined,
) => {
  const [models, setModels] = useState<PropertyModel[]>([]);
  const [criteria, setCriteria] = useState<Record<string, unknown>>(() =>
    sessionProfileId?.trim() ? buildDefaultSearchCriteriaShell() : {},
  );
  const [loading, setLoading] = useState(() =>
    Boolean(sessionProfileId?.trim()),
  );
  const [error, setError] = useState<string | null>(null);
  const criteriaSessionRef = useRef<string | undefined>(undefined);

  const resetAll = () => {
    setModels([]);
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
        setModels([]);
        if (criteriaSessionRef.current !== id) {
          criteriaSessionRef.current = id;
          setCriteria(buildDefaultSearchCriteriaShell());
        }
      }

      try {
        const res = await searchService.search(id, { ...DEFAULT_PAGE });
        if (signal?.aborted) {
          return;
        }

        setModels(toPropertyModels(res.results));
        const c = res.criteria;
        setCriteria(
          c !== null && typeof c === "object" && !Array.isArray(c)
            ? { ...(c as Record<string, unknown>) }
            : {},
        );
      } catch {
        if (signal?.aborted) {
          return;
        }
        setModels([]);
        setError("Could not load search results. Try again later.");
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [sessionProfileId],
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
        await searchService.updateCriteria(id, nextCriteria);
        await load();
      } catch {
        setLoading(false);
        setError("Could not update criteria. Try again later.");
      }
    },
    [load, sessionProfileId],
  );

  useEffect(() => {
    const abortController = new AbortController();
    load(abortController.signal);
    return () => abortController.abort();
  }, [load]);

  return { models, loading, error, criteria, applyCriteria };
};
