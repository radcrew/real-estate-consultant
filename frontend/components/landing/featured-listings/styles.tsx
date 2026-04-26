export const styles = {
  section: "border-b border-border/60 bg-muted/30 px-4 py-14 sm:py-16",
  inner: "mx-auto max-w-screen-xl",
  title:
    "text-center text-2xl font-bold tracking-tight text-foreground sm:text-3xl",
  grid:
    "mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-7 lg:grid-cols-3 lg:gap-8",
  browseRow: "mt-10 flex justify-center sm:mt-12",
  browseButton: "inline-flex items-center gap-2 px-6 font-semibold shadow-none",
  cardLink:
    "group block overflow-hidden rounded-lg border border-border bg-card shadow-sm transition-shadow hover:shadow-md",
  cardImageWrap: "relative aspect-[16/10] bg-muted",
  cardImage:
    "object-cover transition-transform duration-300 group-hover:scale-[1.02]",
  badgeLeftWrap: "absolute left-2 top-2 sm:left-3 sm:top-3",
  badgeLeft:
    "rounded-md bg-background px-2 py-0.5 text-xs font-semibold text-foreground shadow-sm",
  badgeRightWrap: "absolute right-2 top-2 sm:right-3 sm:top-3",
  badgeRight:
    "rounded-md bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground shadow-sm",
  cardBody: "p-4 sm:p-5",
  cardTitle:
    "line-clamp-2 text-base font-bold leading-snug text-foreground sm:text-lg",
  cardLocation: "mt-1.5 text-sm text-muted-foreground",
  cardFooter:
    "mt-4 flex items-end justify-between gap-3 border-t border-border/60 pt-4",
  cardSqft: "text-sm font-bold tabular-nums text-foreground",
  cardPrice: "shrink-0 text-xs font-medium text-muted-foreground",
  cardPriceEmpty: "text-xs text-muted-foreground",
} as const;
