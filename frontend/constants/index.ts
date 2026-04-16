/** Central place for app-wide constants. Add sections as the app grows. */

export const HERO_STATS = [
  { label: "Total Listings", value: "8" },
  { label: "Active Listings", value: "8" },
  { label: "Total SF Available", value: "1,318,500" },
  { label: "Avg Rent/PSF", value: "$18.75" },
] as const

export type HeroStat = (typeof HERO_STATS)[number]
