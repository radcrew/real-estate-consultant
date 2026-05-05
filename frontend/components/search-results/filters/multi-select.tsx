"use client";

import { useMemo } from "react";
import { ChevronDown, X } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { cn } from "@lib/utils";
import { humanizeCriteriaKey } from "@lib/search-criteria";

import { FILTER_BAR_CLUSTER, FILTER_BAR_PILL } from "./styles";

/** Common types shown as checkboxes; merges with current API selections. */
const SUGGESTED_TYPES = [
  "office",
  "coworking",
  "industrial",
  "retail",
  "restaurant",
  "flex",
  "medical",
  "lab",
  "land",
] as const;

const formatOptionLabel = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

type MultiSelectFilterProps = {
  fieldKey: string;
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
  className?: string;
};

export const MultiSelectFilter = ({
  fieldKey,
  value,
  onChange,
  disabled,
  className,
}: MultiSelectFilterProps) => {
  const label = humanizeCriteriaKey(fieldKey);
  const dirty = value.length > 0;

  const options = useMemo(() => {
    const set = new Set<string>([...SUGGESTED_TYPES, ...value.map((x) => x.toLowerCase())]);
    return [...set].sort((a, b) => a.localeCompare(b));
  }, [value]);

  const summaryForAria =
    value.length === 0
      ? "Any"
      : value.length === 1
        ? formatOptionLabel(value[0])
        : `${value.length} selected`;

  const toggle = (opt: string, checked: boolean) => {
    const key = opt.toLowerCase();
    if (checked) {
      if (!value.some((x) => x.toLowerCase() === key)) {
        onChange([...value, opt]);
      }
    } else {
      onChange(value.filter((x) => x.toLowerCase() !== key));
    }
  };

  const triggerInner = (
    <>
      <span className="max-w-[9rem] truncate">{label}</span>
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
            onClick={() => onChange([])}
            disabled={disabled || !dirty}
            aria-label={dirty ? `Clear ${label}` : undefined}
            tabIndex={dirty ? 0 : -1}
          >
            <X className="size-4 shrink-0" aria-hidden />
          </button>
          <DropdownMenuTrigger
            disabled={disabled}
            aria-label={`${label}: ${summaryForAria}`}
            className={cn(FILTER_BAR_PILL, "h-9 shrink-0 rounded-none border-0 shadow-none")}
          >
            {triggerInner}
          </DropdownMenuTrigger>
        </div>
        <DropdownMenuContent align="start" side="bottom" sideOffset={6} className="max-h-72 min-w-[12rem] overflow-y-auto p-1">
          {options.map((opt) => {
            const checked = value.some((x) => x.toLowerCase() === opt.toLowerCase());
            return (
              <DropdownMenuCheckboxItem
                key={opt}
                checked={checked}
                onCheckedChange={(next) => toggle(opt, Boolean(next))}
              >
                {formatOptionLabel(opt)}
              </DropdownMenuCheckboxItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
