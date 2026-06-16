export const STYLES = {
  layout: [
    "grid min-h-0 w-full max-w-6xl flex-1 gap-5",
    "grid-rows-[minmax(0,1fr)_auto] lg:grid-rows-1",
    "lg:grid-cols-[minmax(0,1fr)_minmax(280px,340px)] lg:gap-6",
  ].join(" "),
  chatColumn:
    "flex h-full min-h-0 min-w-0 flex-col rounded-3xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900",
  chatBody: "flex min-h-0 flex-1 flex-col",
  chatHeader: [
    "flex items-center gap-2 border-b border-neutral-200 px-4 py-3 dark:border-neutral-700 sm:px-5",
  ].join(" "),
  chatTitle: "text-sm font-semibold tracking-tight text-foreground sm:text-base",
  messages:
    "flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 py-4 sm:px-5",
  messageRowUser: "flex justify-end gap-2",
  messageRowBot: "flex justify-start gap-2",
  avatarBot:
    "flex size-8 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600 dark:bg-primary-600/15",
  avatarUser:
    "order-2 flex size-8 shrink-0 items-center justify-center rounded-full bg-neutral-200 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200",
  bubbleBot:
    "max-w-[min(100%,34rem)] rounded-2xl rounded-tl-md border border-neutral-200 bg-neutral-50 px-3.5 py-2.5 text-sm leading-relaxed text-foreground dark:border-neutral-700 dark:bg-neutral-800/60",
  bubbleUser:
    "max-w-[min(100%,34rem)] rounded-2xl rounded-tr-md bg-primary-600 px-3.5 py-2.5 text-sm font-medium leading-relaxed text-neutral-50",
  typingBubble:
    "flex items-center gap-2 rounded-2xl rounded-tl-md border border-neutral-200 bg-neutral-50 px-3 py-2 text-sm text-muted-foreground dark:border-neutral-700 dark:bg-neutral-800/60",
  composer: "border-t border-neutral-200 p-3 dark:border-neutral-700 sm:p-4",
  composerInner: "flex items-end gap-2 sm:gap-3",
  textarea: [
    "min-h-0 flex-1 resize-none rounded-2xl border border-neutral-200 bg-white px-4 py-3 text-sm leading-normal",
    "placeholder:text-muted-foreground dark:border-neutral-700 dark:bg-neutral-900",
    "focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-200/50 dark:focus:ring-primary-600/25",
  ].join(" "),
  sendButton:
    "inline-flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary-600 text-neutral-50 transition hover:bg-primary-700 disabled:pointer-events-none disabled:opacity-50",
  sidebar: "flex h-full min-h-0 flex-col gap-4",
  card: [
    "rounded-3xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-900",
  ].join(" "),
  cardHeader: "mb-3 flex items-center gap-2",
  cardTitleRow: "flex items-center gap-2",
  cardTitle: "text-sm font-semibold text-foreground",
  considerCard:
    "rounded-2xl border border-amber-300/80 bg-amber-50/90 p-4 text-sm text-amber-950 shadow-sm dark:border-amber-700/50 dark:bg-amber-950/25 dark:text-amber-50",
  considerTitle: "mb-2 font-semibold",
  considerList: "list-disc space-y-1 pl-4",
  searchCta:
    "inline-flex h-11 w-full items-center justify-center gap-2 rounded-full bg-primary-600 px-4 text-sm font-semibold text-neutral-50 transition hover:bg-primary-700 disabled:pointer-events-none disabled:opacity-50",
  switchLink:
    "flex w-full cursor-pointer items-center justify-center gap-2 border-0 bg-transparent py-2 text-sm font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline",
  loadingWrap: "flex flex-1 items-center justify-center py-16 text-sm text-muted-foreground",
} as const;
