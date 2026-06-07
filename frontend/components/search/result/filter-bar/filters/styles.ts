import { cn } from "@utils/common";

// Voyager TabFilters pill: rounded-full neutral pill, indigo focus/open ring.
export const FILTER_BAR_PILL = cn(
  "inline-flex h-9 min-w-[7.5rem] max-w-[13rem] shrink-0 items-center justify-between gap-2 rounded-full border border-neutral-300 bg-white px-4 text-sm font-medium text-neutral-700",
  "outline-none transition-colors select-none",
  "hover:border-neutral-400 focus-visible:ring-2 focus-visible:ring-primary-200/60",
  "dark:border-neutral-600 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:border-neutral-500",
  "data-[state=open]:border-primary-500 data-[state=open]:ring-2 data-[state=open]:ring-primary-200/50",
);

// Applied on top of FILTER_BAR_PILL when the filter has a value (Voyager's
// filled/selected pill).
export const FILTER_BAR_PILL_ACTIVE = cn(
  "border-primary-500 bg-primary-50 text-primary-700",
  "dark:border-primary-500 dark:bg-primary-600/15 dark:text-primary-200",
);

export const FILTER_BAR_ACTION = "h-9 min-h-9 rounded-full px-4 text-sm font-medium";
