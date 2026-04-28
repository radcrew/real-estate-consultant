export const styles = {
  chooserWrapper:
    "mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center py-10",
  chooserGrid: "mt-8 grid w-full gap-4 md:grid-cols-2",
  choiceCard: [
    "relative flex min-h-[19.75rem] flex-col rounded-xl border border-slate-200",
    "bg-white px-6 py-6 shadow-[0_18px_50px_-40px_rgba(15,23,42,0.35)]",
  ].join(" "),
  bulletRow: "flex items-start gap-2 text-sm leading-6 text-slate-600",
  bulletCheck: "mt-1 size-4 shrink-0 text-emerald-500",
  chooserIntro: "mt-6 max-w-2xl text-center",
  chooserHeading:
    "text-3xl font-semibold tracking-tight text-slate-950 sm:text-4xl",
  chooserSubtitle: "mt-3 text-lg text-slate-500",
  chooserError: [
    "mt-6 w-full max-w-3xl rounded-lg border border-destructive/30 bg-destructive/5",
    "px-4 py-3 text-sm text-destructive",
  ].join(" "),
  choiceIconCellSky:
    "flex size-12 items-center justify-center rounded-lg bg-sky-100 text-blue-600",
  choiceIconCellViolet:
    "flex size-12 items-center justify-center rounded-lg bg-violet-100 text-violet-600",
  choiceCornerBadge: [
    "absolute right-4 top-4 rounded-md bg-violet-600 px-3 py-1 text-xs font-semibold uppercase",
    "tracking-[0.18em] text-white",
  ].join(" "),
  choiceTitle: "text-2xl font-semibold tracking-tight text-slate-950",
  choiceDescription: "mt-3 text-lg leading-8 text-slate-500",
  choiceBullets: "mt-5 space-y-1.5",
  choiceBodyTop: "mt-5",
  choiceFormCta:
    "mt-auto h-11 rounded-md border-slate-200 text-base font-medium shadow-none",
  choiceAiCta: [
    "mt-5 h-11 rounded-md border-violet-700 bg-gradient-to-r from-violet-600 to-indigo-600",
    "text-base font-medium text-white shadow-none hover:from-violet-600 hover:to-indigo-500",
  ].join(" "),
  chooserBackLink: [
    "mt-10 inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-900",
    "transition-colors hover:text-slate-600",
  ].join(" "),
} as const;
