export const styles = {
  summaryGrid: [
    "mt-5 grid gap-4 items-start",
    "lg:grid-cols-[minmax(0,1.35fr)_320px]",
  ].join(" "),
  progressRow: "w-full lg:col-span-2",
  mainColumn: "flex w-full min-w-0 flex-col gap-3",
  summaryColumn: "w-full",
  section: [
    "flex w-full flex-col rounded-xl",
    "border border-border/70 bg-background/90",
    "p-4 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)] sm:p-5",
  ].join(" "),
  errorBanner:
    "mb-4 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive",
  loadingState: "py-10 text-sm text-muted-foreground",
  actionsRow:
    "mt-8 flex flex-col gap-3 border-t border-border/70 pt-6 sm:flex-row sm:items-center sm:justify-between",
  buttonDefault: "h-9 px-3 text-sm",
} as const;
