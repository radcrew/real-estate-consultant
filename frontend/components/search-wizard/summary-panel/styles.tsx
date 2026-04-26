export const styles = {
  panel:
    "flex flex-col rounded-xl border border-border/70 bg-slate-950 p-4 text-slate-100 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.7)] sm:p-5",
  headerStack: "space-y-1.5",
  eyebrow:
    "text-xs font-semibold uppercase tracking-[0.22em] text-amber-200/80",
  title: "text-base font-semibold sm:text-lg",
  rowList: "mt-4 space-y-2.5",
  rowCard: "rounded-lg border border-white/10 bg-white/4 px-3 py-2.5",
  rowStep:
    "text-xs uppercase tracking-[0.18em] text-slate-400",
  rowLabel: "mt-1 text-sm font-medium text-slate-100",
  rowValue: "mt-1 text-sm text-slate-300",
} as const;
