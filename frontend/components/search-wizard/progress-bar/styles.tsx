export const styles = {
  root: "w-full shrink-0",
  header:
    "mb-2 flex items-baseline justify-between gap-3 text-xs text-muted-foreground sm:text-sm",
  stepLabel: "font-medium tabular-nums text-foreground",
  percentLabel: "tabular-nums",
  track:
    "h-1.5 w-full overflow-hidden rounded-full bg-border/70",
  fill: "h-full rounded-full bg-primary transition-[width] duration-300 ease-out",
} as const;
