"use client";

import { createElement, useEffect, useMemo, useState, type ComponentType } from "react";
import { Search } from "lucide-react";

import { buttonVariants } from "@components/ui/buttons";
import { cn } from "@utils/common";
import {
  parseSearchCriteriaEntries,
  getCriteriaFromFilters,
  type ParsedCriteriaEntry,
  type SearchCriterionField,
} from "@lib/search-criteria";

import { MultiSelectFilter } from "./filters/multi-select";
import { CLEAR_RANGE, RangeFilter } from "./filters/range";
import { FILTER_BAR_ACTION } from "./filters/styles";
import { isRangeInvalid } from "./filters/utils";
import { TextFilter } from "./filters/text";

export { SearchFilterSkeleton } from "./skeleton";

type SearchFilterProps = {
  criteria: Record<string, unknown>;
  disabled?: boolean;
  className?: string;
  onSearch?: (nextCriteria: Record<string, unknown>) => void | Promise<void>;
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

const FILTER_COMPONENTS_MAP = {
  location: TextFilter,
  range: RangeFilter,
  "multi-select": MultiSelectFilter,
} as const;

type CriteriaFilterProps = {
  fieldKey: string;
  label: string;
  disabled?: boolean;
  value: unknown;
  unit?: string;
  onChange: (next: unknown) => void;
};

export const SearchFilter = ({ criteria, disabled, className, onSearch }: SearchFilterProps) => {
  const parsed = useMemo(() => parseSearchCriteriaEntries(criteria), [criteria]);
  const sortedParsed = useMemo(() => sortEntries(parsed), [parsed]);

  const [draft, setDraft] = useState<Record<string, SearchCriterionField>>({});

  const hasInvalidRange = useMemo(
    () => Object.values(draft).some((f) => f.type === "range" && isRangeInvalid(f.data)),
    [draft],
  );

  useEffect(() => {
    const next = entriesToDraft(parsed);
    setDraft(cloneCriteriaRecord(next));
  }, [parsed]);

  const updateField = (key: string, field: SearchCriterionField) => {
    setDraft((prev) => ({ ...prev, [key]: field }));
  };

  const handleClear = () => {
    setDraft((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        const filter = next[key];
        if (!filter) {
          continue;
        }
        if (filter.type === "location") {
          next[key] = { ...filter, type: "location", data: "" };
        } else if (filter.type === "range") {
          next[key] = { ...filter, type: "range", data: { ...CLEAR_RANGE } };
        } else if (filter.type === "multi-select") {
          next[key] = { ...filter, type: "multi-select", data: [] };
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
        "flex flex-nowrap items-center gap-2 overflow-hidden py-2",
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

          const Filter = FILTER_COMPONENTS_MAP[field.type] as ComponentType<CriteriaFilterProps>;
          return createElement(Filter, {
            key,
            fieldKey: key,
            label: field.label ?? "",
            disabled,
            value: field.data,
            ...(field.type === "range" ? { unit: field.unit } : {}),
            onChange: (next: unknown) =>
              updateField(key, { ...field, data: next } as SearchCriterionField),
          });
        })}
      </div>

      <div className="ml-auto flex shrink-0 flex-nowrap items-center gap-2">
        <button
          type="button"
          className={cn(
            buttonVariants({ variant: "ghost", size: "lg" }),
            FILTER_BAR_ACTION,
            "text-muted-foreground",
          )}
          onClick={handleClear}
          disabled={disabled}
        >
          Clear
        </button>

        {onSearch != null && (
          <button
            type="button"
            className={cn(
              buttonVariants({ variant: "default", size: "lg" }),
              FILTER_BAR_ACTION,
              "inline-flex gap-1.5 shadow-sm",
            )}
            onClick={() => onSearch(getCriteriaFromFilters(draft))}
            disabled={disabled || hasInvalidRange}
          >
            <Search className="size-4 shrink-0" aria-hidden />
            Search
          </button>
        )}
      </div>
    </section>
  );
};
