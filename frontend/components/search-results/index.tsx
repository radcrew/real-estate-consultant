"use client";

import Link from "next/link";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
import type { SearchResultsChip } from "@lib/search-results-chips";

import { SearchFilter } from "./search-filter";
import { MOCK_RANKED_LISTINGS } from "./mock-data";
import { ResultCard } from "./result-card";
import { ResultsToolbar } from "./results-toolbar";

export const SearchResults = () => {
  const listings = MOCK_RANKED_LISTINGS;
  const chips: SearchResultsChip[] = [];

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-10 sm:py-14">
        <ResultsToolbar resultCount={listings.length} />

        <div className="mb-8">
          <SearchFilter chips={chips} />
        </div>

        {listings.length === 0 ? (
          <p className="py-12 text-center text-muted-foreground">No listings to display.</p>
        ) : (
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
