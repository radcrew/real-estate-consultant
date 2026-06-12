export const STYLES = {
  panel:
    "self-start flex flex-col rounded-3xl border border-neutral-200 bg-white p-6 text-foreground shadow-sm dark:border-neutral-700 dark:bg-neutral-900",
  header:
    "flex items-center justify-between border-b border-neutral-200 pb-3 dark:border-neutral-700",
  headerLeft: "flex items-center gap-2",
  title: "text-sm font-semibold text-foreground",
  badge:
    "inline-flex min-w-6 items-center justify-center rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-semibold text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200",
  placeholder:
    "mt-4 rounded-2xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-muted-foreground dark:border-neutral-700 dark:bg-neutral-800/50",
  rowList: "mt-3 divide-y divide-neutral-200 dark:divide-neutral-700",
  rowItem: "grid grid-cols-[1fr_auto] items-center gap-3 py-2.5",
  rowLabel: "text-sm text-muted-foreground",
  rowValue: "text-sm font-semibold text-foreground",
} as const;
