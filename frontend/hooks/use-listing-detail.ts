"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { getApiErrorMessage } from "@utils/common";
import { listingsService, type ListingDetailResponse } from "@services/listings";

type UseListingDetailResult = {
  data: ListingDetailResponse | null;
  loading: boolean;
  error: string | null;
};

export const useListingDetail = (): UseListingDetailResult => {
  const params = useParams<{ id?: string }>();
  const listingId = (typeof params?.id === "string" ? params.id : "").trim();

  const [data, setData] = useState<ListingDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reset to a fresh loading state when the target listing changes (adjust
  // during render so the effect only owns the async fetch).
  const [prevListingId, setPrevListingId] = useState(listingId);
  if (listingId !== prevListingId) {
    setPrevListingId(listingId);
    setData(null);
    setError(null);
    setLoading(true);
  }

  useEffect(() => {
    if (!listingId) {
      return; // empty id is handled by the derived result below
    }

    const controller = new AbortController();

    listingsService
      .getListing(listingId, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) {
          setData(res);
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(getApiErrorMessage(err));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [listingId]);

  if (!listingId) {
    return { data: null, loading: false, error: "Listing not found." };
  }

  return {
    data,
    loading,
    error,
  };
};
