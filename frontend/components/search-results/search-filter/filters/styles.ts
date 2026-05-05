import { cn } from "@lib/utils";

/** LoopNet-style pill trigger: label left, chevron or clear on the right. */
export const FILTER_BAR_PILL = cn(
  "inline-flex h-9 min-w-[7.5rem] max-w-[13rem] shrink-0 items-center justify-between gap-2 rounded-md border border-border bg-background px-3 text-sm font-semibold text-foreground shadow-sm",
  "outline-none transition-colors select-none",
  "hover:bg-muted/50 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 ring-offset-background",
  "data-[popup-open]:border-foreground/25 data-[popup-open]:bg-muted/40",
);
