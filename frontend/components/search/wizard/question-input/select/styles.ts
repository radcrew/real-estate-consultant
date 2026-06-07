export const STYLES = {
  card:
    "group relative grid min-h-24 grid-rows-[auto_auto_1fr] items-start justify-items-center overflow-hidden rounded-2xl border px-3 py-3.5 text-center transition-all duration-200",
  cardIdle:
    "border-neutral-200 bg-white shadow-sm hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-md dark:border-neutral-700 dark:bg-neutral-900",
  cardSelected:
    "border-primary-600 bg-primary-50 shadow-md dark:border-primary-600 dark:bg-primary-600/15",
  iconWrap:
    "mb-2 inline-flex size-9 items-center justify-center rounded-xl border transition-colors",
  iconWrapIdle:
    "border-neutral-200 bg-neutral-50 text-neutral-500 group-hover:border-primary-200 group-hover:bg-primary-50 group-hover:text-primary-600 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-400",
  iconWrapSelected: "border-primary-200 bg-primary-50 text-primary-600 dark:border-primary-600/40 dark:bg-primary-600/15",
  label: "text-sm font-semibold tracking-tight text-neutral-900 dark:text-neutral-100",
  hint: "mt-1.5 text-xs leading-relaxed text-neutral-500 dark:text-neutral-400",
  textColumn: "flex h-full w-full flex-col",
} as const;
