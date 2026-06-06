"use client";

import { useParams } from "next/navigation";

import { Heading2 } from "@components/ui/voyager/heading2";
import type { PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
import { useVoyagerSearchResults } from "@components/voyager/use-voyager-search-results";
import { cn } from "@utils/common";

import { SearchFilter } from "./filter-bar";

const SKELETON_COUNT = 6;
const GRID = "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3";

const resultCountLabel = (models: PropertyModel[], loading: boolean) => {
  if (loading) {
    return "Searching…";
  }
  return `${models.length} ${models.length === 1 ? "property" : "properties"}`;
};

export const SearchResults = () => {
  const params = useParams<{ id?: string }>();
  const sessionProfileId =
    typeof params?.id === "string" ? params.id : undefined;
  const { models, loading, error, criteria, applyCriteria } =
    useVoyagerSearchResults(sessionProfileId);

  const showFilterDock =
    (loading && !error) || Object.keys(criteria).length > 0;
  const showNoResults =
    !loading && !error && models.length === 0 && Boolean(sessionProfileId?.trim());

  return (
    <div className="min-h-[60vh]">
      {showFilterDock && (
        <div className="fixed top-20 right-0 left-0 z-30 border-b border-neutral-200 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
          <div className="mx-auto max-w-screen-xl px-4 py-2">
            <SearchFilter
              criteria={criteria}
              disabled={loading}
              onSearch={applyCriteria}
            />
          </div>
        </div>
      )}

      <div
        className={cn(
          "mx-auto max-w-screen-xl px-4 pb-12",
          showFilterDock ? "pt-16" : "pt-10",
        )}
      >
        {error && (
          <p className="py-6 text-center text-red-600 dark:text-red-400">
            {error}
          </p>
        )}

        {!error && (
          <Heading2
            heading="Properties"
            subHeading={
              <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
                {resultCountLabel(models, loading)}
              </span>
            }
          />
        )}

        {loading && !error && (
          <div
            className={GRID}
            role="status"
            aria-live="polite"
            aria-label="Loading search results"
          >
            {Array.from({ length: SKELETON_COUNT }, (_, i) => (
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
        )}

        {!loading && !error && models.length > 0 && (
          <div className={GRID}>
            {models.map((model) => (
              <PropertyCard key={model.id} data={model} />
            ))}
          </div>
        )}

        {showNoResults && (
          <p className="py-16 text-center text-neutral-500 dark:text-neutral-400">
            No properties match your search.
          </p>
        )}
      </div>
    </div>
  );
};
