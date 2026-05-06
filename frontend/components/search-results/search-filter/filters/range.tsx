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

import { FILTER_BAR_PILL } from "./styles";
import { stopMenuKeyboardCapture, stopMenuTriggerBubble } from "./utils";

type RangeFilterProps = {
  fieldKey: string;
  label: string;
  value: RangeCriterionData;
  onChange: (next: RangeCriterionData) => void;
  disabled?: boolean;
  className?: string;
};

const fmt = (n: number) =>
  new Intl.NumberFormat("en-US", {
    maximumFractionDigits: n >= 1000 ? 0 : 2,
    notation: n >= 1e6 ? "compact" : "standard",
  }).format(n);

export const CLEAR_RANGE: RangeCriterionData = { min: Number.NaN, max: Number.NaN };

function rangeTriggerText(value: RangeCriterionData, label: string) {
  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    return `${fmt(value.min)} – ${fmt(value.max)}`;
  }
  if (Number.isFinite(value.min)) {
    return `From ${fmt(value.min)}`;
  }
  if (Number.isFinite(value.max)) {
    return `To ${fmt(value.max)}`;
  }
  return label;
}

function rangeSummaryForAria(value: RangeCriterionData) {
  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    return `${fmt(value.min)} to ${fmt(value.max)}`;
  }
  if (Number.isFinite(value.min)) {
    return `minimum ${fmt(value.min)}`;
  }
  if (Number.isFinite(value.max)) {
    return `maximum ${fmt(value.max)}`;
  }
  return "Not set";
}

export const RangeFilter = ({ fieldKey, label, value, onChange, disabled, className }: RangeFilterProps) => {
  const hasValue = Number.isFinite(value.min) || Number.isFinite(value.max);
  const summary = rangeSummaryForAria(value);
  const triggerText = rangeTriggerText(value, label);

  const setBound = (bound: "min" | "max", raw: string) => {
    const t = raw.trim();
    if (t === "") {
      onChange({ ...value, [bound]: Number.NaN });
      return;
    }
    const n = Number(raw);
    if (Number.isFinite(n)) {
      onChange({ ...value, [bound]: n });
    }
  };

  const handleClear = (e: { preventDefault: () => void; stopPropagation: () => void }) => {
    stopMenuTriggerBubble(e);
    onChange(CLEAR_RANGE);
  };

  return (
    <div className={cn("shrink-0", className)}>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger
          disabled={disabled}
          aria-label={`${label}: ${summary}`}
          className={cn(FILTER_BAR_PILL, "disabled:pointer-events-none disabled:opacity-50")}
        >
          <span className="min-w-0 flex-1 truncate text-left">{triggerText}</span>
          {hasValue ? (
            <span
              title={`Clear ${label}`}
              className="-mr-1 flex size-8 shrink-0 cursor-default items-center justify-center rounded-sm text-muted-foreground hover:bg-muted hover:text-foreground"
              onPointerDown={stopMenuTriggerBubble}
              onClick={handleClear}
            >
              <X className="size-4 shrink-0" aria-hidden />
            </span>
          ) : (
            <ChevronDown className="size-4 shrink-0 text-muted-foreground pointer-events-none" aria-hidden />
          )}
        </DropdownMenuTrigger>
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
                  onChange={(e) => setBound("min", e.target.value)}
                  onKeyDownCapture={stopMenuKeyboardCapture}
                  disabled={disabled}
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
                  onChange={(e) => setBound("max", e.target.value)}
                  onKeyDownCapture={stopMenuKeyboardCapture}
                  disabled={disabled}
                />
              </div>
            </div>
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
