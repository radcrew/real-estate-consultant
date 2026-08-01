"use client";

import { useEffect, useState } from "react";

import {
  PROPERTY_GRID,
  PropertyCard,
  PropertyCardSkeleton,
} from "@components/property/card";
import { toPropertyModels } from "@components/property/listing-model";
import { listingsService } from "@services/listings";
import type { PropertyModel } from "@typings/property";

type ListingSimilarSectionProps = {
  listingId: string;
};

/**
 * Embedding-ranked neighbors for the listing detail page.
 * Soft-fails (hides) when embeddings are unavailable or the request errors.
 */
export const ListingSimilarSection = ({ listingId }: ListingSimilarSectionProps) => {
  const [models, setModels] = useState<PropertyModel[] | null>(null);

  useEffect(() => {
    if (!listingId) {
      setModels([]);
      return;
    }

    setModels(null);
    const controller = new AbortController();
    listingsService
      .getSimilarListings(listingId, { limit: 6, signal: controller.signal })
      .then((res) => {
        if (!controller.signal.aborted) {
          setModels(toPropertyModels(Array.isArray(res.results) ? res.results : []));
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setModels([]);
        }
      });

    return () => controller.abort();
  }, [listingId]);

  const loading = models === null;
  if (!loading && models.length === 0) {
    return null;
  }

  return (
    <section
      className="mt-10"
      aria-labelledby="listing-similar"
      aria-busy={loading || undefined}
    >
      <h2
        id="listing-similar"
        className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100"
      >
        Similar listings
      </h2>
      <p className="mt-1 text-neutral-500 dark:text-neutral-400">
        Nearby properties ranked by listing similarity.
      </p>
      <div className="my-5 w-14 border-b border-neutral-200 dark:border-neutral-700" />
      <div className={PROPERTY_GRID}>
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <PropertyCardSkeleton key={i} />)
          : models.map((item) => <PropertyCard key={item.id} data={item} />)}
      </div>
    </section>
  );
};
