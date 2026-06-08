"use client";

import { useEffect, useState } from "react";

import { useSavedListings } from "@components/saved/provider";
import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { detailToModel, type PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
import { listingsService } from "@services/listings";

const GRID = "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3";

export const SavedView = () => {
  const { savedIds, isSaved, ready, signedIn } = useSavedListings();
  const [models, setModels] = useState<PropertyModel[] | null>(null);

  useEffect(() => {
    if (!ready || !signedIn) {
      return;
    }
    if (models !== null) {
      return; // fetch listing details only once
    }

    let cancelled = false;
    void (async () => {
      if (savedIds.length === 0) {
        if (!cancelled) setModels([]);
        return;
      }
      const results = await Promise.allSettled(
        savedIds.map((id) => listingsService.getListing(id)),
      );
      if (cancelled) return;
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
  }, [ready, signedIn, savedIds, models]);

  const loading = signedIn && (!ready || models === null);
  // Reflect un-saves immediately without refetching.
  const visible = (models ?? []).filter((m) => isSaved(m.id));

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
          Saved properties
        </h1>
        <p className="mt-3 text-neutral-500 dark:text-neutral-400">
          {!signedIn
            ? "Sign in to view and save properties."
            : loading
              ? "Loading your saved properties…"
              : `${visible.length} ${visible.length === 1 ? "property" : "properties"} saved.`}
        </p>
      </div>

      {ready && !signedIn ? (
        <div className="mt-12 rounded-2xl border border-neutral-200 p-10 text-center dark:border-neutral-700">
          <p className="text-neutral-600 dark:text-neutral-300">
            Sign in to save properties and see them here.
          </p>
          <div className="mt-6 flex justify-center">
            <ButtonPrimary href="/sign-in">Sign in</ButtonPrimary>
          </div>
        </div>
      ) : null}

      {loading ? (
        <div className={`mt-10 ${GRID}`} role="status" aria-label="Loading saved properties">
          {Array.from({ length: 3 }, (_, i) => (
            <div
              key={i}
              className="overflow-hidden rounded-2xl border border-neutral-100 dark:border-neutral-800"
            >
              <div className="aspect-[4/3] animate-pulse bg-neutral-100 dark:bg-neutral-800" />
              <div className="space-y-3 p-4">
                <div className="h-4 w-1/3 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
                <div className="h-5 w-4/5 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {signedIn && !loading && visible.length === 0 ? (
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

      {signedIn && !loading && visible.length > 0 ? (
        <div className={`mt-10 ${GRID}`}>
          {visible.map((model) => (
            <PropertyCard key={model.id} data={model} />
          ))}
        </div>
      ) : null}
    </div>
  );
};
