/** Central place for app-wide constants. Add sections as the app grows. */

export const HERO_STATS = [
  { label: "Total Listings", value: "8" },
  { label: "Active Listings", value: "8" },
  { label: "Total SF Available", value: "1,318,500" },
  { label: "Avg Rent/PSF", value: "$18.75" },
] as const

export type HeroStat = (typeof HERO_STATS)[number]

export type FeaturedListingCategory = "Industrial" | "Flex" | "Retail"

export type FeaturedListingTransaction = "Lease" | "Sale"

export type FeaturedListing = {
  id: string
  category: FeaturedListingCategory
  transactionType: FeaturedListingTransaction
  title: string
  location: string
  sqftLabel: string
  priceLabel: string | null
  imageSrc: string
  imageAlt: string
}

export const FEATURED_LISTINGS: FeaturedListing[] = [
  {
    id: "1",
    category: "Industrial",
    transactionType: "Lease",
    title: "Prime Industrial Distribution Center",
    location: "Midlothian, IL · Chicago South Suburbs",
    sqftLabel: "250,000 SF",
    priceLabel: "$6.5/psf",
    imageSrc:
      "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=900&h=560&q=80",
    imageAlt: "Industrial warehouse exterior",
  },
  {
    id: "2",
    category: "Retail",
    transactionType: "Lease",
    title: "High-Street Retail Corner Suite",
    location: "Naperville, IL · Western Suburbs",
    sqftLabel: "12,400 SF",
    priceLabel: "$28/psf",
    imageSrc:
      "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&h=560&q=80",
    imageAlt: "Retail storefront",
  },
  {
    id: "3",
    category: "Industrial",
    transactionType: "Lease",
    title: "Cross-Dock Logistics Facility",
    location: "Gary, IN · Northwest Indiana",
    sqftLabel: "410,000 SF",
    priceLabel: "$5.25/psf",
    imageSrc: "https://images.unsplash.com/photo-1578575437130-527eed3abbec?w=800",
    imageAlt: "Loading docks at distribution center",
  },
  {
    id: "4",
    category: "Industrial",
    transactionType: "Sale",
    title: "Cold Storage & Food-Grade Industrial",
    location: "Indianapolis, IN · Indianapolis Metro",
    sqftLabel: "185,000 SF",
    priceLabel: "$42.5M",
    imageSrc:
      "https://images.unsplash.com/photo-1581092160562-40aa08e78837?auto=format&fit=crop&w=900&h=560&q=80",
    imageAlt: "Cold storage facility interior",
  },
  {
    id: "5",
    category: "Retail",
    transactionType: "Sale",
    title: "Neighborhood Shopping Center Pad",
    location: "Schaumburg, IL · O'Hare Corridor",
    sqftLabel: "38,500 SF",
    priceLabel: "$12.2M",
    imageSrc: "https://images.unsplash.com/photo-1553413077-190dd305871c?w=800",
    imageAlt: "Shopping plaza aerial",
  },
  {
    id: "6",
    category: "Flex",
    transactionType: "Lease",
    title: "Urban Last-Mile Flex Warehouse",
    location: "Chicago, IL · Chicago",
    sqftLabel: "28,000 SF",
    priceLabel: "$16.5/psf",
    imageSrc:
      "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=900&h=560&q=80",
    imageAlt: "Modern flex office and warehouse",
  },
]
