export const styles = {
  overlay: [
    "fixed inset-0 z-50 flex min-h-screen",
    "bg-slate-950/70 backdrop-blur-sm",
  ].join(" "),
  panel: [
    "flex min-h-screen w-full flex-col overflow-hidden",
    "bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.98))]",
    "text-foreground",
  ].join(" "),
  content: [
    "mx-auto flex min-h-0 w-full max-w-5xl flex-1 flex-col",
    "px-4 pt-5 pb-6 sm:px-6 lg:px-8",
  ].join(" "),
} as const;
