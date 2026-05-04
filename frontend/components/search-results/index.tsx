"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { useIntakeSessions } from "@hooks/use-intake-sessions";
import { chipsFromIntakeCriteria, type SearchResultsChip } from "@lib/search-results-chips";
import { cn } from "@lib/utils";

import { SearchFilter } from "./search-filter";
import { MOCK_RANKED_LISTINGS } from "./mock-data";
import { ResultCard } from "./result-card";
import { ResultsToolbar } from "./results-toolbar";

export const SearchResults = () => {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");
  const { getSession } = useIntakeSessions();

  const [chips, setChips] = useState<SearchResultsChip[]>([]);
  const [criteriaState, setCriteriaState] = useState<
    "loading" | "ready" | "error" | "no-session"
  >(() => (sessionId ? "loading" : "no-session"));

  useEffect(() => {
    if (!sessionId) {
      setChips([]);
      setCriteriaState("no-session");
      return;
    }

    let cancelled = false;
    setCriteriaState("loading");
    setChips([]);

    void getSession(sessionId)
      .then((session) => {
        if (cancelled) {
          return;
        }
        const next = chipsFromIntakeCriteria(session.criteria);
        setChips(next);
        setCriteriaState("ready");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setChips([]);
        setCriteriaState("error");
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId, getSession]);

  const listings = MOCK_RANKED_LISTINGS;

  const criteriaBlock =
    criteriaState === "no-session" ? (
      <div className="mb-8 rounded-lg border border-dashed border-border bg-card/50 px-4 py-6 text-center sm:px-6">
        <p className="text-sm text-muted-foreground">
          Open this page from a completed search (with a{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">session</code> in the URL) to see
          your criteria here, or{" "}
          <Link href="/questionnaire" className="font-medium text-primary underline-offset-4 hover:underline">
            start a search
          </Link>
          .
        </p>
      </div>
    ) : criteriaState === "loading" ? (
      <div className="mb-8 rounded-lg border border-border bg-card/50 px-4 py-6 text-center text-sm text-muted-foreground sm:px-6">
        Loading your search criteria…
      </div>
    ) : criteriaState === "error" ? (
      <div className="mb-8 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-6 text-center text-sm text-destructive sm:px-6">
        We couldn&apos;t load criteria for this session. Try{" "}
        <Link href="/questionnaire" className="font-medium underline-offset-4 hover:underline">
          starting a new search
        </Link>
        .
      </div>
    ) : chips.length > 0 ? (
      <div className="mb-8">
        <SearchFilter chips={chips} />
      </div>
    ) : (
      <div className="mb-8 rounded-lg border border-dashed border-border bg-card/50 px-4 py-6 text-center sm:px-6">
        <p className="text-sm text-muted-foreground">
          No criteria fields returned for this session yet. You can still browse demo listings below.
        </p>
      </div>
    );

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-10 sm:py-14">
        <ResultsToolbar resultCount={listings.length} />

        {criteriaBlock}

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
