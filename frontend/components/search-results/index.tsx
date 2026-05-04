"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
import { useSearchSessionResults } from "@hooks/use-search-session-results";

import { ResultCard } from "./result-card";
import { ResultsToolbar } from "./results-toolbar";

export const SearchResults = () => {
  const params = useParams<{ id?: string }>();
  const sessionProfileId = typeof params?.id === "string" ? params.id : undefined;
  const { listings, loading, error } = useSearchSessionResults(sessionProfileId);

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-10 sm:py-14">
        <ResultsToolbar />

        {error && <p className="py-6 text-center text-destructive">{error}</p>}

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
