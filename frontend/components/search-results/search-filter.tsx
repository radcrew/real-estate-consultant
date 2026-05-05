"use client";

import { useEffect, useMemo, useState } from "react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
import {
  parseSearchCriteriaEntries,
  type ParsedCriteriaEntry,
  type RangeCriterion,
  type SearchCriterionField,
} from "@lib/search-criteria";

import { MultiSelectFilter } from "./filters/multi-select";
import { RangeFilter } from "./filters/range";
import { TextFilter } from "./filters/text";

type SearchFilterProps = {
  criteria: Record<string, unknown>;
  disabled?: boolean;
  className?: string;
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

export const SearchFilter = ({ criteria, disabled, className }: SearchFilterProps) => {
  const parsed = useMemo(() => parseSearchCriteriaEntries(criteria), [criteria]);
  const sortedParsed = useMemo(() => sortEntries(parsed), [parsed]);

  const [draft, setDraft] = useState<Record<string, SearchCriterionField>>({});
  const [initialDraft, setInitialDraft] = useState<Record<string, SearchCriterionField>>({});

  useEffect(() => {
    const next = entriesToDraft(parsed);
    setDraft(cloneCriteriaRecord(next));
    setInitialDraft(cloneCriteriaRecord(next));
  }, [parsed]);

  const updateField = (key: string, field: SearchCriterionField) => {
    setDraft((prev) => ({ ...prev, [key]: field }));
  };

  const clearAll = () => {
    setDraft(cloneCriteriaRecord(initialDraft));
  };

  if (sortedParsed.length === 0) {
    return null;
  }

  return (
    <section
      className={cn(
        "flex flex-wrap items-center gap-2 rounded-lg border border-border bg-background p-2 shadow-sm",
        disabled && "pointer-events-none opacity-60",
        className,
      )}
      aria-label="Search criteria filters"
    >
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
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
            case "range": {
              const init =
                initialDraft[key]?.type === "range"
                  ? initialDraft[key].data
                  : (field as RangeCriterion).data;
              return (
                <RangeFilter
                  key={key}
                  fieldKey={key}
                  value={field.data}
                  initial={init}
                  onChange={(next) => updateField(key, { type: "range", data: next })}
                  disabled={disabled}
                />
              );
            }
            case "multi-select": {
              const initList =
                initialDraft[key]?.type === "multi-select" ? initialDraft[key].data : field.data;
              return (
                <MultiSelectFilter
                  key={key}
                  fieldKey={key}
                  value={field.data}
                  initial={initList}
                  onChange={(next) => updateField(key, { type: "multi-select", data: next })}
                  disabled={disabled}
                />
              );
            }
          }
        })}
      </div>

      <button
        type="button"
        className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "shrink-0 text-muted-foreground")}
        onClick={clearAll}
        disabled={disabled}
      >
        Clear
      </button>
    </section>
  );
};
