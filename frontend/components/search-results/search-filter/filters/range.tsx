"use client";

import { ChevronDown, X } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { Input } from "@components/ui/input";
import { cn, formatMetricNumber, formatMoney } from "@lib/utils";
import type { RangeCriterionData } from "@lib/search-criteria";

import { FILTER_BAR_PILL } from "./styles";
import { stopMenuKeyboardCapture, stopMenuTriggerBubble } from "./utils";

type RangeFilterProps = {
  fieldKey: string;
  label: string;
  unit?: string;
  value: RangeCriterionData;
  onChange: (next: RangeCriterionData) => void;
  disabled?: boolean;
  className?: string;
};

export const CLEAR_RANGE: RangeCriterionData = { min: Number.NaN, max: Number.NaN };

function rangeTriggerText(value: RangeCriterionData, label: string, unit?: string) {
  const u = unit?.trim();
  const uUpper = u?.toUpperCase() ?? "";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  const hasMin = Number.isFinite(value.min);
  const hasMax = Number.isFinite(value.max);

  if (hasBounds) {
    if (uUpper === "USD") {
      return `USD ${formatMoney(value.min, { integerThreshold: 1000 })} – ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    const suffix = u ? ` ${u}` : "";
    return `${formatMetricNumber(value.min)} – ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (hasMin) {
    if (uUpper === "USD") {
      return `From ${formatMoney(value.min, { integerThreshold: 1000 })}`;
    }
    const suffix = u ? ` ${u}` : "";
    return `From ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (hasMax) {
    if (uUpper === "USD") {
      return `Up to ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    const suffix = u ? ` ${u}` : "";
    return `Up to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (u) {
    return `${label} (${u})`;
  }
  return label;
}

function rangeSummaryForAria(value: RangeCriterionData, unit?: string) {
  const u = unit?.trim();
  const suffix = u ? ` ${u}` : "";
  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    return `${formatMetricNumber(value.min)} to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (Number.isFinite(value.min)) {
    return `minimum ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (Number.isFinite(value.max)) {
    return `maximum ${formatMetricNumber(value.max)}${suffix}`;
  }
  return "Not set";
}

export const RangeFilter = ({
  fieldKey,
  label,
  unit,
  value,
  onChange,
  disabled,
  className,
}: RangeFilterProps) => {
  const hasValue = Number.isFinite(value.min) || Number.isFinite(value.max);
  const summary = rangeSummaryForAria(value, unit);
  const triggerText = rangeTriggerText(value, label, unit);

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
            <div className="text-xs font-medium text-muted-foreground">
              {label}
              {unit != null && unit.trim().length > 0 ? (
                <span className="font-normal text-muted-foreground"> ({unit.trim()})</span>
              ) : null}
            </div>
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
