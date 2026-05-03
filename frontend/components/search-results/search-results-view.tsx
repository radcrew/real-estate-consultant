"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { getSearchResultsHandoffSnapshot } from "@lib/search-results-handoff";
import { cn } from "@lib/utils";

import { SearchFilter } from "./search-filter";
import { MOCK_RANKED_LISTINGS } from "./mock-data";
import { ResultCard } from "./result-card";
import { ResultsToolbar } from "./results-toolbar";

const handoffSubscribe = () => () => {};

export const SearchResultsView = () => {
  const handoff = useSyncExternalStore(
    handoffSubscribe,
    getSearchResultsHandoffSnapshot,
    () => null,
  );
  const chips = handoff?.chips ?? [];

  const listings = MOCK_RANKED_LISTINGS;

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-10 sm:py-14">
        <ResultsToolbar resultCount={listings.length} />

        {chips.length > 0 ? (
          <div className="mb-8">
            <SearchFilter chips={chips} />
          </div>
        ) : (
          <div className="mb-8 rounded-lg border border-dashed border-border bg-card/50 px-4 py-6 text-center sm:px-6">
            <p className="text-sm text-muted-foreground">
              No saved criteria in this tab session. You can still browse ranked demo listings
              below, or{" "}
              <Link href="/questionnaire" className="font-medium text-primary underline-offset-4 hover:underline">
                start a search
              </Link>{" "}
              to see your requirements summarized here.
            </p>
          </div>
        )}

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
