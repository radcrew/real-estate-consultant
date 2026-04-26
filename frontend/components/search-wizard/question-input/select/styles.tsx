export const styles = {
  card:
    "group relative grid min-h-24 grid-rows-[auto_auto_1fr] items-start justify-items-center overflow-hidden rounded-xl border px-3 py-3.5 text-center transition-all duration-200",
  cardIdle:
    "border-slate-200/90 bg-white shadow-[0_8px_24px_-18px_rgba(15,23,42,0.35)] hover:-translate-y-0.5 hover:border-amber-300/70 hover:shadow-[0_20px_45px_-28px_rgba(245,158,11,0.45)]",
  cardSelected:
    "border-amber-400 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,247,237,0.96))] shadow-[0_18px_40px_-24px_rgba(245,158,11,0.6)]",
  iconWrap:
    "mb-2 inline-flex size-9 items-center justify-center rounded-lg border transition-colors",
  iconWrapIdle:
    "border-slate-200 bg-slate-50 text-slate-500 group-hover:border-amber-200 group-hover:bg-amber-50 group-hover:text-amber-500",
  iconWrapSelected: "border-amber-200 bg-amber-50 text-amber-500",
  label: "text-sm font-semibold tracking-tight text-slate-950",
  hint: "mt-1.5 text-xs leading-relaxed text-slate-500",
  textColumn: "flex h-full w-full flex-col",
} as const;
