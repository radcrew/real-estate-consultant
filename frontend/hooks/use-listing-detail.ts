"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { getApiErrorMessage } from "@lib/api-errors";
import { listingsService, type ListingDetailResponse } from "@services/listings";

type UseListingDetailResult = {
  data: ListingDetailResponse | null;
  loading: boolean;
  error: string | null;
};

export const useListingDetail = (): UseListingDetailResult => {
  const params = useParams<{ id?: string }>();
  const listingId = typeof params?.id === "string" ? params.id : "";

  const [data, setData] = useState<ListingDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = listingId.trim();
    if (!id) {
      setError("Listing not found.");
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(null);

    listingsService
      .getListing(id, { signal: controller.signal })
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

  return {
    data,
    loading,
    error,
  };
};
