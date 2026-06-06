export const STYLES = {
  section: "relative px-4 pt-10 pb-16 sm:pt-14 lg:pt-20",
  inner:
    "mx-auto flex max-w-screen-xl flex-col-reverse items-center gap-10 lg:flex-row lg:gap-14",
  left: "flex w-full flex-col items-start space-y-7 sm:space-y-9 lg:w-1/2",
  headline:
    "text-4xl font-medium leading-[114%] text-neutral-900 md:text-5xl xl:text-6xl dark:text-neutral-100",
  subcopy: "text-base text-neutral-500 md:text-lg dark:text-neutral-400",
  imageWrap: "relative aspect-[4/3] w-full overflow-hidden rounded-3xl lg:w-1/2",
  statsSection:
    "mx-auto mt-16 w-full max-w-screen-xl border-t border-neutral-200 px-4 pt-10 dark:border-neutral-700",
  statsGrid:
    "grid w-full grid-cols-2 place-items-center gap-x-14 gap-y-12 text-center sm:grid-cols-4",
  statCell: "flex flex-col items-center justify-center gap-1 text-center",
  statValue: "text-2xl font-bold tabular-nums text-primary-600 sm:text-3xl",
  statLabel:
    "text-[0.65rem] font-medium tracking-wider text-neutral-500 uppercase sm:text-xs dark:text-neutral-400",
} as const;
