"use client";

import { useMemo, useState } from "react";
import { LayoutGrid, Map as MapIcon } from "lucide-react";
import { useParams } from "next/navigation";

import { NoticeCard } from "@components/ui/notice-card";
import type { PropertyModel } from "@components/voyager/listing-model";
import {
  PropertyCard,
  PropertyCardSkeleton,
  PROPERTY_GRID,
} from "@components/voyager/property-card";
import { Pagination } from "@components/ui/voyager/pagination";
import { SectionGridHasMap } from "@components/voyager/section-grid-has-map";
import { useVoyagerSearchResults } from "@components/voyager/use-voyager-search-results";
import { cn } from "@utils/common";

import { SearchFilter } from "./filter-bar";

type View = "grid" | "map";

const SKELETON_COUNT = 6;
const PAGE_SIZE = 9;
const TOGGLE_BTN =
  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors";

const resultCountLabel = (models: PropertyModel[], loading: boolean) =>
  loading
    ? "Searching…"
    : `${models.length} ${models.length === 1 ? "property" : "properties"}`;

export const SearchResults = () => {
  const params = useParams<{ id?: string }>();
  const sessionProfileId =
    typeof params?.id === "string" ? params.id : undefined;
  const { models, loading, error, criteria, applyCriteria } =
    useVoyagerSearchResults(sessionProfileId);
  const [view, setView] = useState<View>("grid");
  const [page, setPage] = useState(0);

  // Reset to the first page whenever the result set changes (adjust during render).
  const [prevModels, setPrevModels] = useState(models);
  if (models !== prevModels) {
    setPrevModels(models);
    setPage(0);
  }

  const pageCount = Math.ceil(models.length / PAGE_SIZE);
  const pagedModels = useMemo(
    () => models.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE),
    [models, page],
  );

  const showFilterDock =
    (loading && !error) || Object.keys(criteria).length > 0;
  const showNoResults =
    !loading && !error && models.length === 0 && Boolean(sessionProfileId?.trim());
  const hasResults = !loading && !error && models.length > 0;

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
          "mx-auto px-4 pb-12",
          view === "map" ? "max-w-[1600px]" : "max-w-screen-xl",
          showFilterDock ? "pt-16" : "pt-10",
        )}
      >
        {error && (
          <div className="mt-4 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-center text-sm text-destructive">
            {error}
          </div>
        )}

        {!error && (
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="text-3xl font-semibold text-neutral-900 sm:text-4xl dark:text-neutral-100">
                Properties
              </h2>
              <span className="mt-2 block text-neutral-500 dark:text-neutral-400">
                {resultCountLabel(models, loading)}
              </span>
            </div>

            {hasResults && (
              <div className="inline-flex shrink-0 rounded-full border border-neutral-200 p-1 dark:border-neutral-700">
                <button
                  type="button"
                  onClick={() => setView("grid")}
                  className={cn(
                    TOGGLE_BTN,
                    view === "grid"
                      ? "bg-primary-600 text-white"
                      : "text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white",
                  )}
                  aria-pressed={view === "grid"}
                >
                  <LayoutGrid className="h-4 w-4" aria-hidden />
                  Grid
                </button>
                <button
                  type="button"
                  onClick={() => setView("map")}
                  className={cn(
                    TOGGLE_BTN,
                    view === "map"
                      ? "bg-primary-600 text-white"
                      : "text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white",
                  )}
                  aria-pressed={view === "map"}
                >
                  <MapIcon className="h-4 w-4" aria-hidden />
                  Map
                </button>
              </div>
            )}
          </div>
        )}

        {loading && !error && (
          <div
            className={PROPERTY_GRID}
            role="status"
            aria-live="polite"
            aria-label="Loading search results"
          >
            {Array.from({ length: SKELETON_COUNT }, (_, i) => (
              <PropertyCardSkeleton key={i} />
            ))}
          </div>
        )}

        {hasResults &&
          (view === "grid" ? (
            <>
              <div className={PROPERTY_GRID}>
                {pagedModels.map((model) => (
                  <PropertyCard key={model.id} data={model} />
                ))}
              </div>

              {pageCount > 1 && (
                <div className="mt-12 flex justify-center">
                  <Pagination
                    items={Array.from({ length: pageCount }, (_, i) => ({
                      label: String(i + 1),
                    }))}
                    activeIndex={page}
                    onPageClick={(i) => {
                      setPage(i);
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                  />
                </div>
              )}
            </>
          ) : (
            <SectionGridHasMap data={models} />
          ))}

        {showNoResults && (
          <NoticeCard className="mt-4">
            <p className="text-neutral-700 dark:text-neutral-200">
              No properties match your search.
            </p>
            <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
              Try widening your filters — adjust price, size, or property type above.
            </p>
          </NoticeCard>
        )}
      </div>
    </div>
  );
};
