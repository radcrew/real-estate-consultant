"use client";

import { ChevronDown, X } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { Input } from "@components/ui/input";
import { cn } from "@lib/utils";
import type { RangeCriterionData } from "@lib/search-criteria";
import { humanizeCriteriaKey } from "@lib/search-criteria";

import { FILTER_BAR_CLUSTER, FILTER_BAR_PILL } from "./styles";

type RangeFilterProps = {
  fieldKey: string;
  value: RangeCriterionData;
  initial: RangeCriterionData;
  onChange: (next: RangeCriterionData) => void;
  disabled?: boolean;
  className?: string;
};

const fmt = (n: number) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: n >= 1000 ? 0 : 2, notation: n >= 1e6 ? "compact" : "standard" }).format(n);

const sameRange = (a: RangeCriterionData, b: RangeCriterionData) => a.min === b.min && a.max === b.max;

export const RangeFilter = ({ fieldKey, value, initial, onChange, disabled, className }: RangeFilterProps) => {
  const label = humanizeCriteriaKey(fieldKey);
  const summary = `${fmt(value.min)} – ${fmt(value.max)}`;
  const dirty = !sameRange(value, initial);
  const triggerLabel = label.replace(/\s+range$/i, "").trim() || label;

  const setMin = (raw: string) => {
    const n = Number(raw);
    if (Number.isFinite(n)) {
      onChange({ ...value, min: n });
    }
  };

  const setMax = (raw: string) => {
    const n = Number(raw);
    if (Number.isFinite(n)) {
      onChange({ ...value, max: n });
    }
  };

  const triggerInner = (
    <>
      <span className="max-w-[9rem] truncate">{triggerLabel}</span>
      <ChevronDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
    </>
  );

  return (
    <div className={cn("shrink-0", className)}>
      <DropdownMenu modal={false}>
        <div className={FILTER_BAR_CLUSTER}>
          <button
            type="button"
            className={cn(
              "flex min-h-9 w-9 shrink-0 items-center justify-center border-r text-muted-foreground transition-opacity hover:bg-muted hover:text-foreground",
              dirty ? "visible border-border" : "invisible pointer-events-none border-transparent",
            )}
            onClick={() => onChange({ ...initial })}
            disabled={disabled || !dirty}
            aria-label={dirty ? `Reset ${label}` : undefined}
            tabIndex={dirty ? 0 : -1}
          >
            <X className="size-4 shrink-0" aria-hidden />
          </button>
          <DropdownMenuTrigger
            disabled={disabled}
            aria-label={`${label}: ${summary}`}
            className={cn(FILTER_BAR_PILL, "h-9 shrink-0 rounded-none border-0 shadow-none")}
          >
            {triggerInner}
          </DropdownMenuTrigger>
        </div>
        <DropdownMenuContent align="start" side="bottom" sideOffset={6} className="min-w-[16rem] p-3">
          <div className="space-y-3">
            <div className="text-xs font-medium text-muted-foreground">{label}</div>
            <div className="flex gap-3">
              <div className="min-w-0 flex-1 space-y-1">
                <label className="text-xs text-muted-foreground" htmlFor={`${fieldKey}-min`}>
                  Min
                </label>
                <Input
                  id={`${fieldKey}-min`}
                  type="number"
                  value={Number.isFinite(value.min) ? value.min : ""}
                  onChange={(e) => setMin(e.target.value)}
                />
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <label className="text-xs text-muted-foreground" htmlFor={`${fieldKey}-max`}>
                  Max
                </label>
                <Input
                  id={`${fieldKey}-max`}
                  type="number"
                  value={Number.isFinite(value.max) ? value.max : ""}
                  onChange={(e) => setMax(e.target.value)}
                />
              </div>
            </div>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
