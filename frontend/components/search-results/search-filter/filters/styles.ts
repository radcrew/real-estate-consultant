import { cn } from "@lib/utils";

/** LoopNet-style pill trigger for criteria dropdowns. */
export const FILTER_BAR_PILL = cn(
  "inline-flex h-9 shrink-0 items-center gap-1.5 rounded-md border border-border bg-background px-3 text-sm font-medium text-foreground shadow-sm",
  "outline-none transition-colors select-none",
  "hover:bg-muted/50 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 ring-offset-background",
  "data-[popup-open]:border-foreground/25 data-[popup-open]:bg-muted/40",
);

export const FILTER_BAR_CLUSTER = cn(
  "inline-flex h-9 shrink-0 items-stretch overflow-hidden rounded-md border border-border bg-background shadow-sm",
  "focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/50 focus-within:ring-offset-2 ring-offset-background",
);
