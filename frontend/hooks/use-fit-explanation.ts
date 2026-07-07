"use client";

import { useCallback, useState } from "react";

import { searchService, type FitExplanation } from "@services/search";
import { getApiErrorMessage } from "@utils/common";

type UseFitExplanationResult = {
  cache: Record<string, FitExplanation>;
  loadingId: string | null;
  errors: Record<string, string>;
  explain: (propertyId: string) => Promise<FitExplanation | undefined>;
};

/**
 * Lazy, per-property fit explanations for a search session.
 *
 * Generate-on-demand (mirrors `useOutreachDraft`), not eagerly for every
 * result: an LLM call per visible card would be slow and expensive for
 * explanations most users won't open. Results are cached in memory for the
 * lifetime of this hook instance (one search-results page view).
 */
export const useFitExplanation = (
  sessionProfileId: string | undefined,
): UseFitExplanationResult => {
  const [cache, setCache] = useState<Record<string, FitExplanation>>({});
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const explain = useCallback(
    async (propertyId: string) => {
      const id = sessionProfileId?.trim();
      if (!id) {
        return undefined;
      }
      const cached = cache[propertyId];
      if (cached) {
        return cached;
      }

      setLoadingId(propertyId);
      setErrors((prev) =>
        propertyId in prev
          ? Object.fromEntries(
              Object.entries(prev).filter(([key]) => key !== propertyId),
            )
          : prev,
      );
      try {
        const result = await searchService.explainFit(id, propertyId);
        setCache((prev) => ({ ...prev, [propertyId]: result }));
        return result;
      } catch (err: unknown) {
        setErrors((prev) => ({ ...prev, [propertyId]: getApiErrorMessage(err) }));
        return undefined;
      } finally {
        setLoadingId((current) => (current === propertyId ? null : current));
      }
    },
    [sessionProfileId, cache],
  );

  return { cache, loadingId, errors, explain };
};
