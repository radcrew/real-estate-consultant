export const styles = {
  layout: [
    "mt-4 grid w-full max-w-6xl gap-5 lg:gap-6",
    "lg:grid-cols-[minmax(0,1fr)_minmax(280px,340px)]",
  ].join(" "),
  chatColumn: "flex min-h-[420px] min-w-0 flex-col rounded-xl border border-border/70 bg-background/95 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.55)]",
  chatHeader: [
    "flex items-center gap-2 border-b border-border/60 px-4 py-3 sm:px-5",
  ].join(" "),
  chatTitle: "text-sm font-semibold tracking-tight text-foreground sm:text-base",
  messages: "flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4 sm:px-5",
  messageRowUser: "flex justify-end gap-2",
  messageRowBot: "flex justify-start gap-2",
  avatarBot:
    "flex size-8 shrink-0 items-center justify-center rounded-full bg-violet-100 text-violet-600",
  avatarUser:
    "order-2 flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700",
  bubbleBot:
    "max-w-[min(100%,34rem)] rounded-2xl rounded-tl-md border border-border/60 bg-muted/40 px-3.5 py-2.5 text-sm leading-relaxed text-foreground",
  bubbleUser:
    "max-w-[min(100%,34rem)] rounded-2xl rounded-tr-md bg-amber-400 px-3.5 py-2.5 text-sm font-medium leading-relaxed text-amber-950",
  composer: "border-t border-border/60 p-3 sm:p-4",
  composerInner: "flex gap-2 sm:gap-3",
  textarea: [
    "min-h-[88px] flex-1 resize-y rounded-lg border border-border/80 bg-background px-3 py-2.5 text-sm",
    "placeholder:text-muted-foreground shadow-sm",
    "focus-visible:outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40",
  ].join(" "),
  sendButton:
    "inline-flex size-11 shrink-0 items-center justify-center rounded-lg bg-amber-400 text-amber-950 shadow-sm transition hover:bg-amber-500 disabled:pointer-events-none disabled:opacity-50",
  sidebar: "flex flex-col gap-4",
  card: [
    "rounded-xl border border-border/70 bg-background/95 p-4 shadow-[0_16px_50px_-40px_rgba(15,23,42,0.45)]",
  ].join(" "),
  cardHeader: "mb-3 flex items-center justify-between gap-2",
  cardTitleRow: "flex items-center gap-2",
  cardTitle: "text-sm font-semibold text-foreground",
  badgeCount:
    "inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-foreground",
  criteriaTable: "space-y-2 text-sm",
  criteriaRow: "flex justify-between gap-3 border-b border-border/40 py-1.5 last:border-0",
  criteriaLabel: "text-muted-foreground",
  criteriaValue: "text-right font-medium text-foreground",
  missingCard:
    "rounded-xl border border-amber-300/80 bg-amber-50/90 p-4 text-sm text-amber-950 shadow-sm dark:border-amber-700/50 dark:bg-amber-950/25 dark:text-amber-50",
  missingTitle: "mb-2 font-semibold",
  missingList: "list-disc space-y-1 pl-4",
  searchCta:
    "inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-amber-400 px-4 text-sm font-semibold text-amber-950 shadow-sm transition hover:bg-amber-500 disabled:pointer-events-none disabled:opacity-50",
  switchLink:
    "flex w-full cursor-pointer items-center justify-center gap-2 border-0 bg-transparent py-2 text-sm font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline",
  loadingWrap: "flex flex-1 items-center justify-center py-16 text-sm text-muted-foreground",
  errorBanner:
    "mb-3 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive",
} as const;
