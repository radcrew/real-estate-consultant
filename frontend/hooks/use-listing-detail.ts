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

  const [fetchedId, setFetchedId] = useState<string | null>(null);
  const [data, setData] = useState<ListingDetailResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!listingId) return;

    setFetchedId(null);
    setData(null);
    setError(null);

    const controller = new AbortController();

    listingsService
      .getListing(listingId, { signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) {
          setData(res);
          setFetchedId(listingId);
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(getApiErrorMessage(err));
          setFetchedId(listingId);
        }
      });

    return () => controller.abort();
  }, [listingId]);

  if (!listingId) {
    return { data: null, loading: false, error: "Listing not found." };
  }

  return {
    data,
    loading: fetchedId !== listingId,
    error,
  };
};
