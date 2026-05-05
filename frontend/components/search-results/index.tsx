"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
import { useSearchSessionResults } from "@hooks/use-search-session-results";

import { ResultCard } from "./result-card";
import { SearchFilter } from "./search-filter";

const SKELETON_COUNT = 6;

export const SearchResults = () => {
  const params = useParams<{ id?: string }>();
  const sessionProfileId = typeof params?.id === "string" ? params.id : undefined;
  const { listings, loading, error, criteria, refetch } = useSearchSessionResults(sessionProfileId);

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-10 sm:py-14">
        <div className="mb-8">
          <SearchFilter criteria={criteria} disabled={loading} onSearch={refetch} />
        </div>

        {error && <p className="py-6 text-center text-destructive">{error}</p>}

        {loading && !error && (
          <div
            className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-7 lg:grid-cols-3 lg:gap-8"
            role="status"
            aria-live="polite"
            aria-label="Loading search results"
          >
            {Array.from({ length: SKELETON_COUNT }, (_, i) => (
              <div
                key={i}
                className="overflow-hidden rounded-lg border border-border bg-card shadow-sm"
              >
                <div className="aspect-[4/3] animate-pulse bg-muted" />
                <div className="space-y-3 p-4">
                  <div className="h-5 w-[85%] max-w-[14rem] animate-pulse rounded-md bg-muted" />
                  <div className="h-4 w-[55%] max-w-[10rem] animate-pulse rounded-md bg-muted" />
                  <div className="h-12 w-full animate-pulse rounded-md bg-muted" />
                  <div className="flex justify-between gap-4 pt-1">
                    <div className="h-4 w-16 animate-pulse rounded-md bg-muted" />
                    <div className="h-4 w-20 animate-pulse rounded-md bg-muted" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && !error && listings.length > 0 && (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-7 lg:grid-cols-3 lg:gap-8">
            {listings.map((listing) => (
              <ResultCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}

        <div className="mt-12 flex justify-center border-t border-border pt-10">
          <Link
            href="/listings"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }), "inline-flex gap-2")}
          >
            <Search className="size-5 shrink-0" aria-hidden />
            Browse all properties
          </Link>
        </div>
      </div>
    </div>
  );
};
