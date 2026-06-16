export const STYLES = {
  chooserWrapper:
    "mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center py-10",
  chooserGrid: "mt-8 grid w-full gap-5 md:grid-cols-2",
  choiceCard: [
    "relative flex min-h-[19.75rem] flex-col rounded-3xl border border-neutral-200",
    "bg-white px-7 py-7 shadow-sm transition-shadow hover:shadow-md",
    "dark:border-neutral-700 dark:bg-neutral-900",
  ].join(" "),
  bulletRow:
    "flex items-start gap-2 text-sm leading-6 text-neutral-600 dark:text-neutral-300",
  bulletCheck: "mt-1 size-4 shrink-0 text-primary-600",
  chooserIntro: "mt-6 max-w-2xl text-center",
  chooserHeading:
    "text-3xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100 sm:text-4xl",
  chooserSubtitle: "mt-3 text-lg text-neutral-500 dark:text-neutral-400",
  choiceIconCellSky:
    "flex size-12 items-center justify-center rounded-2xl bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200",
  choiceIconCellViolet:
    "flex size-12 items-center justify-center rounded-2xl bg-primary-50 text-primary-600 dark:bg-primary-600/15",
  choiceCornerBadge: [
    "absolute right-5 top-5 rounded-full bg-primary-600 px-3 py-1 text-xs font-semibold uppercase",
    "tracking-[0.18em] text-neutral-50",
  ].join(" "),
  choiceTitle:
    "text-2xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100",
  choiceDescription: "mt-3 text-lg leading-8 text-neutral-500 dark:text-neutral-400",
  choiceBullets: "mt-5 space-y-1.5",
  choiceBodyTop: "mt-5",
  choiceFormCta: "mt-auto w-full",
  choiceAiCta: "mt-5 w-full",
  chooserBackLink: [
    "mt-10 inline-flex cursor-pointer items-center gap-2 text-sm font-medium",
    "text-neutral-700 transition-colors hover:text-neutral-900",
    "dark:text-neutral-300 dark:hover:text-neutral-100",
  ].join(" "),
} as const;
