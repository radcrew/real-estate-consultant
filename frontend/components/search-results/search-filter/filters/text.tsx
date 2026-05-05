"use client";

import { MapPin, Search, X } from "lucide-react";

import { Input } from "@components/ui/input";
import { cn } from "@lib/utils";

type TextFilterProps = {
  fieldKey: string;
  label: string;
  value: string;
  onChange: (next: string) => void;
  disabled?: boolean;
  className?: string;
};

/** Compact location field for single-row filter bar. */
export const TextFilter = ({ fieldKey, label, value, onChange, disabled, className }: TextFilterProps) => {
  return (
    <div
      className={cn(
        "relative flex h-9 w-52 shrink-0 items-center rounded-md border border-border bg-background shadow-sm",
        disabled && "pointer-events-none opacity-50",
        className,
      )}
    >
      <MapPin className="pointer-events-none absolute left-2.5 size-4 text-muted-foreground" aria-hidden />
      <Input
        id={`${fieldKey}-text`}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={cn(
          "h-9 border-0 bg-transparent pl-9 pr-20 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0",
          value ? "pr-24" : "pr-12",
        )}
        placeholder={label}
        aria-label={label}
      />
      {value ? (
        <button
          type="button"
          className="absolute right-9 rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          onClick={() => onChange("")}
          disabled={disabled}
          aria-label={label ? `Clear ${label}` : "Clear"}
        >
          <X className="size-4" aria-hidden />
        </button>
      ) : null}
      <Search className="pointer-events-none absolute right-2.5 size-4 text-muted-foreground" aria-hidden />
    </div>
  );
};
