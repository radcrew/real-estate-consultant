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
      "https://images.pexels.com/photos/1268871/pexels-photo-1268871.jpeg?auto=compress&cs=tinysrgb&w=800",
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
      "https://images.pexels.com/photos/1179156/pexels-photo-1179156.jpeg?auto=compress&cs=tinysrgb&w=800",
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
    imageSrc:
      "https://images.pexels.com/photos/2506988/pexels-photo-2506988.jpeg?auto=compress&cs=tinysrgb&w=800",
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
      "https://images.pexels.com/photos/2373201/pexels-photo-2373201.jpeg?auto=compress&cs=tinysrgb&w=800",
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
    imageSrc:
      "https://images.pexels.com/photos/6434634/pexels-photo-6434634.jpeg?auto=compress&cs=tinysrgb&w=800",
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
      "https://images.pexels.com/photos/3201735/pexels-photo-3201735.jpeg?auto=compress&cs=tinysrgb&w=800",
    imageAlt: "Modern flex office and warehouse",
  },
]
