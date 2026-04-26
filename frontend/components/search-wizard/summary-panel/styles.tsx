export const styles = {
  panel:
    "self-start flex flex-col rounded-xl border border-border/70 bg-background/90 p-4 text-foreground shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
  header:
    "flex items-center justify-between border-b border-border/70 pb-3",
  headerLeft: "flex items-center gap-2",
  title: "text-sm font-semibold text-foreground",
  badge:
    "inline-flex min-w-6 items-center justify-center rounded bg-muted px-2 py-0.5 text-xs font-semibold text-foreground",
  placeholder:
    "mt-4 rounded-lg border border-border/70 bg-background px-3 py-2.5 text-sm text-muted-foreground",
  rowList: "mt-3 divide-y divide-border/70",
  rowItem: "grid grid-cols-[1fr_auto] items-center gap-3 py-2.5",
  rowLabel: "text-sm text-muted-foreground",
  rowValue: "text-sm font-semibold text-foreground",
} as const;
