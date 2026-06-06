export const STYLES = {
  section: "px-4 py-16 lg:py-20",
  inner: "mx-auto max-w-screen-xl",
  grid: "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3",
  browseRow: "mt-14 flex justify-center",
  card: "group relative flex flex-col overflow-hidden rounded-2xl border border-neutral-100 bg-white transition-shadow hover:shadow-xl dark:border-neutral-800 dark:bg-neutral-900",
  imageWrap:
    "relative aspect-[4/3] w-full overflow-hidden bg-neutral-100 dark:bg-neutral-800",
  image: "object-cover transition-transform duration-300 group-hover:scale-105",
  body: "flex flex-1 flex-col space-y-3 p-4",
  meta: "text-sm text-neutral-500 dark:text-neutral-400",
  title: "text-base font-semibold text-neutral-900 capitalize dark:text-white",
  location:
    "flex items-center space-x-1.5 text-sm text-neutral-500 dark:text-neutral-400",
  divider: "w-14 border-b border-neutral-100 dark:border-neutral-800",
  footer: "mt-auto flex items-center justify-between pt-1",
  sqft: "text-base font-semibold text-neutral-900 dark:text-white",
  price: "text-sm font-medium text-neutral-500 dark:text-neutral-400",
} as const;
