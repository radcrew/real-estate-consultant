"use client";

import Link from "next/link";
import { ArrowLeft, Loader2, Sparkles } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";

type ResultsToolbarProps = {
  loading?: boolean;
};

export const ResultsToolbar = ({ loading = false }: ResultsToolbarProps) => (
  <div className="flex flex-col gap-4 border-b border-border pb-6">
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
      <Link
        href="/"
        className={cn(
          buttonVariants({ variant: "ghost", size: "sm" }),
          "inline-flex shrink-0 gap-1.5 self-start no-underline",
        )}
      >
        <ArrowLeft className="size-4" aria-hidden />
        Home
      </Link>
      <div className="flex flex-wrap gap-2 sm:ml-auto">
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
      </div>
    </div>

    <div>
      <div className="flex items-center gap-2 text-amber-600">
        <Sparkles className="size-5 shrink-0" aria-hidden />
        <span className="text-xs font-semibold uppercase tracking-wide">Ranked for you</span>
      </div>
      <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
        Property matches
      </h1>
      {loading && (
        <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 shrink-0 animate-spin" aria-hidden />
          <span>Loading matches…</span>
        </p>
      )}
    </div>
  </div>
);
