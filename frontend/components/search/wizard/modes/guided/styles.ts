export const STYLES = {
  summaryGrid: [
    "mt-5 grid gap-5 items-start pt-8 sm:pt-10 lg:pt-12",
    "lg:grid-cols-[minmax(0,1.35fr)_320px]",
  ].join(" "),
  progressRow: "w-full lg:col-span-2",
  mainColumn: "flex w-full min-w-0 flex-col gap-3",
  summaryColumn: "w-full",
  section: [
    "flex w-full flex-col rounded-3xl",
    "border border-neutral-200 bg-white p-6 shadow-sm sm:p-7",
    "dark:border-neutral-700 dark:bg-neutral-900",
  ].join(" "),
  loadingState: "py-10 text-sm text-muted-foreground",
  actionsRow:
    "mt-8 flex flex-col gap-3 border-t border-neutral-200 pt-6 dark:border-neutral-700 sm:flex-row sm:items-center sm:justify-between",
} as const;
