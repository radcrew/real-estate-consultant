"use client";

import { useEffect, useState } from "react";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { detailToModel, type PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
import { getSavedListingIds } from "@lib/saved-listings";
import { listingsService } from "@services/listings";

const GRID = "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3";

const SavedPage = () => {
  const [models, setModels] = useState<PropertyModel[] | null>(null);

  useEffect(() => {
    const ids = getSavedListingIds();
    if (ids.length === 0) {
      setModels([]);
      return;
    }

    let cancelled = false;
    void (async () => {
      const results = await Promise.allSettled(
        ids.map((id) => listingsService.getListing(id)),
      );
      if (cancelled) {
        return;
      }
      const loaded = results
        .filter((r): r is PromiseFulfilledResult<Awaited<ReturnType<typeof listingsService.getListing>>> =>
          r.status === "fulfilled",
        )
        .map((r) => detailToModel(r.value));
      setModels(loaded);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const loading = models === null;

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
          Saved properties
        </h1>
        <p className="mt-3 text-neutral-500 dark:text-neutral-400">
          {loading
            ? "Loading your saved properties…"
            : `${models.length} ${models.length === 1 ? "property" : "properties"} saved.`}
        </p>
      </div>

      {!loading && models.length === 0 ? (
        <div className="mt-12 rounded-2xl border border-neutral-200 p-10 text-center dark:border-neutral-700">
          <p className="text-neutral-600 dark:text-neutral-300">
            You haven&rsquo;t saved any properties yet. Tap the heart on a listing
            to save it here.
          </p>
          <div className="mt-6 flex justify-center">
            <ButtonPrimary href="/listings">Browse properties</ButtonPrimary>
          </div>
        </div>
      ) : null}

      {!loading && models.length > 0 ? (
        <div className={`mt-10 ${GRID}`}>
          {models.map((model) => (
            <PropertyCard key={model.id} data={model} />
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default SavedPage;
