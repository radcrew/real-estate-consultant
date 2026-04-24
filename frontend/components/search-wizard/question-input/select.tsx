"use client";

import { Check } from "lucide-react";

import { cn } from "@lib/utils";

type SelectOptionCardProps = {
  label: string;
  hint?: string;
  selected: boolean;
  rounded?: boolean;
  onClick: () => void;
};

export const SelectOptionCard = ({
  label,
  hint,
  selected,
  rounded = true,
  onClick,
}: SelectOptionCardProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "flex min-h-36 flex-col justify-between border p-5 text-left transition-colors",
      selected
        ? "border-primary bg-primary/12"
        : "border-border/70 bg-background hover:bg-muted/50",
    )}
  >
    <div className="flex items-start justify-between gap-4">
      <span className="text-lg font-semibold">{label}</span>
      <span
        className={cn(
          "inline-flex size-6 items-center justify-center border",
          rounded && "rounded-full",
          selected
            ? "border-primary bg-primary text-primary-foreground"
            : "border-border/80 bg-background",
        )}
      >
        {selected && <Check className="size-3.5" aria-hidden />}
      </span>
    </div>
    <span className="text-sm text-muted-foreground">{hint}</span>
  </button>
);
