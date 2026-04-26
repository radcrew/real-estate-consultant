export const styles = {
  section:
    "relative border-b border-border/60 bg-gradient-to-br from-amber-200/25 via-background to-background px-4 pt-16 pb-10 sm:py-16",
  inner: "mx-auto flex max-w-3xl flex-col items-center text-center",
  headlineStack: "flex flex-col items-center gap-1 sm:gap-1.5",
  headlineStrip:
    "px-3 py-1.5 text-2xl font-bold text-foreground sm:px-4 sm:py-2 sm:text-4xl sm:leading-tight md:text-5xl",
  subcopy:
    "mt-6 max-w-xl text-pretty text-base text-muted-foreground sm:text-lg",
  statsSection:
    "mx-auto mt-14 flex w-full max-w-3xl flex-col items-center justify-center border-t border-border/60 px-4 pt-10",
  statsGrid:
    "grid w-full grid-cols-2 place-items-center gap-x-14 gap-y-16 text-center sm:grid-cols-4 sm:gap-x-16 sm:gap-y-14",
  statCell:
    "flex flex-col items-center justify-center gap-1 text-center",
  statValue: "text-2xl font-bold tabular-nums text-primary sm:text-3xl",
  statLabel:
    "text-[0.65rem] font-medium uppercase tracking-wider text-muted-foreground sm:text-xs",
} as const;
