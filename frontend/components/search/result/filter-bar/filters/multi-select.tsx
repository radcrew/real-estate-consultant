"use client";

import { useMemo } from "react";
import { ChevronDown, X } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { cn } from "@utils/common";

import { FILTER_BAR_PILL } from "./styles";
import { stopMenuTriggerBubble } from "./utils";

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
  label: string;
  value: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
  className?: string;
};

const multiTriggerText = (value: string[], label: string) => {
  if (value.length === 0) {
    return label;
  }
  if (value.length === 1) {
    return formatOptionLabel(value[0]);
  }
  return `${formatOptionLabel(value[0])} +${value.length - 1}`;
}

export const MultiSelectFilter = ({ label, value, onChange, disabled, className }: MultiSelectFilterProps) => {
  const hasValue = value.length > 0;

  const options = useMemo(() => {
    const set = new Set<string>([...SUGGESTED_TYPES, ...value.map((x) => x.toLowerCase())]);
    return [...set].sort((a, b) => a.localeCompare(b));
  }, [value]);

  const summaryForAria =
    value.length === 0 ? "Any" : value.length === 1 ? formatOptionLabel(value[0]) : `${value.length} selected`;

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

  const triggerText = multiTriggerText(value, label);

  const handleClear = (e: { preventDefault: () => void; stopPropagation: () => void }) => {
    stopMenuTriggerBubble(e);
    onChange([]);
  };

  return (
    <div className={cn("shrink-0", className)}>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger
          disabled={disabled}
          aria-label={`${label}: ${summaryForAria}`}
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
