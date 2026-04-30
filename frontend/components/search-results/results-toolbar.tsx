"use client";

import Link from "next/link";
import { ArrowLeft, Pencil, Sparkles } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";

export type ResultsSortOption = "match" | "size" | "title";

type ResultsToolbarProps = {
  resultCount: number;
  sortBy: ResultsSortOption;
  onSortChange: (value: ResultsSortOption) => void;
};

export const ResultsToolbar = ({
  resultCount,
  sortBy,
  onSortChange,
}: ResultsToolbarProps) => (
  <div className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <div className="flex items-center gap-2 text-amber-600">
        <Sparkles className="size-5 shrink-0" aria-hidden />
        <span className="text-xs font-semibold uppercase tracking-wide">Ranked for you</span>
      </div>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        Property matches
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {resultCount === 0
          ? "No listings to show yet."
          : `${resultCount} propert${resultCount === 1 ? "y" : "ies"} ranked by fit (demo data).`}
      </p>
    </div>

    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <label className="flex items-center gap-2 text-sm text-muted-foreground">
        <span className="whitespace-nowrap font-medium text-foreground">Sort</span>
        <select
          className={cn(
            "h-9 min-w-[10.5rem] border border-border bg-background px-2 text-sm font-medium text-foreground",
            "outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 ring-offset-background",
          )}
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as ResultsSortOption)}
        >
          <option value="match">Best match</option>
          <option value="size">Size (SF)</option>
          <option value="title">Title (A–Z)</option>
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        <Link
          href="/questionnaire"
          className={cn(
            buttonVariants({ variant: "outline", size: "sm" }),
            "inline-flex gap-1.5 no-underline",
          )}
        >
          <Pencil className="size-4" aria-hidden />
          Edit search
        </Link>
        <Link
          href="/questionnaire"
          className={cn(
            buttonVariants({ variant: "secondary", size: "sm" }),
            "inline-flex gap-1.5 no-underline",
          )}
        >
          <Sparkles className="size-4" aria-hidden />
          New search
        </Link>
        <Link
          href="/"
          className={cn(
            buttonVariants({ variant: "ghost", size: "sm" }),
            "inline-flex gap-1.5 no-underline",
          )}
        >
          <ArrowLeft className="size-4" aria-hidden />
          Home
        </Link>
      </div>
    </div>
  </div>
);
