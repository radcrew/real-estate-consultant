/** Full-viewport overlay must start below the global header (``top-16``) and stay at or below its z-index. */
export const styles = {
  overlay: [
    "fixed inset-x-0 bottom-0 top-16 z-30 flex flex-col",
    "bg-slate-950/70 backdrop-blur-sm",
  ].join(" "),
  panel: [
    "flex min-h-0 w-full flex-1 flex-col overflow-hidden",
    "bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.98))]",
    "text-foreground",
  ].join(" "),
  content: [
    "mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col",
    "px-4 pt-5 pb-6 sm:px-6 lg:px-8",
  ].join(" "),
} as const;
