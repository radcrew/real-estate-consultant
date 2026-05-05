"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
import {
  parseSearchCriteriaEntries,
  type ParsedCriteriaEntry,
  type SearchCriterionField,
} from "@lib/search-criteria";

import { MultiSelectFilter } from "./filters/multi-select";
import { CLEAR_RANGE, RangeFilter } from "./filters/range";
import { TextFilter } from "./filters/text";

type SearchFilterProps = {
  criteria: Record<string, unknown>;
  disabled?: boolean;
  className?: string;
  /** Re-runs the search request (e.g. after adjusting filters). */
  onSearch?: () => void;
};

const entriesToDraft = (entries: ParsedCriteriaEntry[]): Record<string, SearchCriterionField> =>
  Object.fromEntries(entries.map(({ key, field }) => [key, field]));

const cloneCriteriaRecord = (r: Record<string, SearchCriterionField>): Record<string, SearchCriterionField> =>
  JSON.parse(JSON.stringify(r)) as Record<string, SearchCriterionField>;

const sortEntries = (entries: ParsedCriteriaEntry[]): ParsedCriteriaEntry[] => {
  const rank = (e: ParsedCriteriaEntry) => {
    if (e.field.type === "location") {
      return 0;
    }
    if (e.field.type === "multi-select") {
      return 1;
    }
    return 2;
  };
  return [...entries].sort((a, b) => rank(a) - rank(b) || a.key.localeCompare(b.key));
};

export const SearchFilter = ({ criteria, disabled, className, onSearch }: SearchFilterProps) => {
  const parsed = useMemo(() => parseSearchCriteriaEntries(criteria), [criteria]);
  const sortedParsed = useMemo(() => sortEntries(parsed), [parsed]);

  const [draft, setDraft] = useState<Record<string, SearchCriterionField>>({});

  useEffect(() => {
    const next = entriesToDraft(parsed);
    setDraft(cloneCriteriaRecord(next));
  }, [parsed]);

  const updateField = (key: string, field: SearchCriterionField) => {
    setDraft((prev) => ({ ...prev, [key]: field }));
  };

  const clearAll = () => {
    setDraft((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        const f = next[key];
        if (!f) {
          continue;
        }
        if (f.type === "location") {
          next[key] = { type: "location", data: "" };
        } else if (f.type === "range") {
          next[key] = { type: "range", data: { ...CLEAR_RANGE } };
        } else if (f.type === "multi-select") {
          next[key] = { type: "multi-select", data: [] };
        }
      }
      return next;
    });
  };

  if (sortedParsed.length === 0) {
    return null;
  }

  return (
    <section
      className={cn(
        "flex flex-nowrap items-center gap-2 overflow-hidden rounded-lg border border-border bg-background p-2 shadow-sm",
        disabled && "pointer-events-none opacity-60",
        className,
      )}
      aria-label="Search criteria filters"
    >
      <div className="flex min-w-0 flex-1 flex-nowrap items-center gap-2 overflow-x-auto [scrollbar-width:thin]">
        {sortedParsed.map(({ key }) => {
          const field = draft[key];
          if (!field) {
            return null;
          }

          switch (field.type) {
            case "location":
              return (
                <TextFilter
                  key={key}
                  fieldKey={key}
                  value={field.data}
                  onChange={(next) => updateField(key, { type: "location", data: next })}
                  disabled={disabled}
                />
              );
            case "range":
              return (
                <RangeFilter
                  key={key}
                  fieldKey={key}
                  value={field.data}
                  onChange={(next) => updateField(key, { type: "range", data: next })}
                  disabled={disabled}
                />
              );
            case "multi-select":
              return (
                <MultiSelectFilter
                  key={key}
                  fieldKey={key}
                  value={field.data}
                  onChange={(next) => updateField(key, { type: "multi-select", data: next })}
                  disabled={disabled}
                />
              );
          }
        })}
      </div>

      <div className="ml-auto flex shrink-0 flex-nowrap items-center gap-2">
        <button
          type="button"
          className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-muted-foreground")}
          onClick={clearAll}
          disabled={disabled}
        >
          Clear
        </button>
        {onSearch != null && (
          <button
            type="button"
            className={cn(buttonVariants({ variant: "default", size: "sm" }), "inline-flex gap-1.5")}
            onClick={onSearch}
            disabled={disabled}
          >
            <Search className="size-4 shrink-0" aria-hidden />
            Search
          </button>
        )}
      </div>
    </section>
  );
};

/** Placeholder bar matching ``SearchFilter`` layout while results load. */
export const SearchFilterSkeleton = ({ className }: { className?: string }) => (
  <section
    className={cn(
      "flex flex-nowrap items-center gap-2 overflow-hidden rounded-lg border border-border bg-background p-2 shadow-sm",
      className,
    )}
    aria-busy="true"
    aria-label="Loading search filters"
  >
    <div className="flex min-w-0 flex-1 flex-nowrap items-center gap-2 overflow-x-hidden">
      <div className="h-9 w-52 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-28 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-32 shrink-0 animate-pulse rounded-md bg-muted" />
    </div>
    <div className="ml-auto flex shrink-0 gap-2">
      <div className="h-9 w-14 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-20 shrink-0 animate-pulse rounded-md bg-muted" />
    </div>
  </section>
);
