import Link from "next/link";
import { Search } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { HERO_STATS } from "@/constants";
import { cn } from "@/lib/utils";

const HERO_SECTION =
  "relative border-b border-border/60 bg-gradient-to-br from-amber-200/25 via-background to-background px-4 pt-16 pb-10 sm:py-16";

const HERO_INNER =
  "mx-auto flex max-w-3xl flex-col items-center text-center";

const HERO_HEADLINE_STACK = "flex flex-col items-center gap-1 sm:gap-1.5";

const HERO_HEADLINE_STRIP =
  "px-3 py-1.5 text-2xl font-bold text-foreground sm:px-4 sm:py-2 sm:text-4xl sm:leading-tight md:text-5xl";

const HERO_SUBCOPY =
  "mt-6 max-w-xl text-pretty text-base text-muted-foreground sm:text-lg";

const HERO_CTA_ROW = "mt-8 flex flex-wrap items-center justify-center gap-3";

const HERO_PRIMARY_CTA_EXTRA =
  "inline-flex h-11 min-h-11 items-center gap-2.5 px-7 text-base font-semibold shadow-none";

const HERO_OUTLINE_CTA_EXTRA =
  "h-11 min-h-11 border-border bg-background px-7 text-base font-semibold shadow-none";

const HERO_STATS_SECTION =
  "mx-auto mt-14 flex w-full max-w-3xl flex-col items-center justify-center border-t border-border/60 px-4 pt-10";

const HERO_STATS_GRID =
  "grid w-full grid-cols-2 place-items-center gap-x-14 gap-y-16 text-center sm:grid-cols-4 sm:gap-x-16 sm:gap-y-14";

const HERO_STAT_CELL =
  "flex flex-col items-center justify-center gap-1 text-center";

const HERO_STAT_VALUE =
  "text-2xl font-bold tabular-nums text-primary sm:text-3xl";

const HERO_STAT_LABEL =
  "text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground sm:text-xs";

export const Hero = () => (
  <section className={HERO_SECTION}>
    <div className={HERO_INNER}>
      <div className={HERO_HEADLINE_STACK}>
        <span className={HERO_HEADLINE_STRIP}>Find Your Next Commercial</span>
        <span className={HERO_HEADLINE_STRIP}>Property with AI</span>
      </div>

      <p className={HERO_SUBCOPY}>
        Professional-grade CRE platform with AI-powered fit scoring, broker-style
        search, and outreach draft generation.
      </p>

      <div className={HERO_CTA_ROW}>
        <Link
          href="/sign-up"
          className={cn(buttonVariants({ size: "lg" }), HERO_PRIMARY_CTA_EXTRA)}
        >
          <Search className="size-5 shrink-0" aria-hidden />
          Start Searching
        </Link>
        <Link
          href="/sign-in"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            HERO_OUTLINE_CTA_EXTRA
          )}
        >
          Sign In
        </Link>
      </div>

    </div>
    <div className={HERO_STATS_SECTION}>
      <div className={HERO_STATS_GRID}>
        {HERO_STATS.map(({ label, value }) => (
          <div key={label} className={HERO_STAT_CELL}>
            <p className={HERO_STAT_VALUE}>{value}</p>
            <p className={HERO_STAT_LABEL}>{label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
)
