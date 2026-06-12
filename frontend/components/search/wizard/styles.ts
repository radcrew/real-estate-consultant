export const STYLES = {
  overlay: [
    "fixed inset-x-0 bottom-0 top-16 z-30 flex flex-col",
    "bg-neutral-900/60 backdrop-blur-sm",
  ].join(" "),
  panel: [
    "flex min-h-0 w-full flex-1 flex-col overflow-hidden",
    "bg-neutral-100 text-foreground dark:bg-neutral-950",
  ].join(" "),
  content: [
    "mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col",
    "px-4 pt-5 pb-6 sm:px-6 lg:px-8",
  ].join(" "),
} as const;
