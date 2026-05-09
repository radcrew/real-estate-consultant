/** Stand-in for `GET /api/v1/listings/{id}` until the client is wired up. */

export type MockListingProperty = {
  id: string;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  property_type: string | null;
  listing_type: string | null;
  description: string | null;
  size_sqft: number | null;
  price: number | null;
  rent: number | null;
  clear_height: number | null;
  loading_docks: number | null;
  image: string | null;
};

export type MockListingDetail = {
  property: MockListingProperty;
  images: string[];
};

const IMG = [
  "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1600&q=80&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1600&q=80&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1553413077-190dd305871c?w=1600&q=80&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&q=80&auto=format&fit=crop",
] as const;

export const MOCK_LISTING_DETAIL: MockListingDetail = {
  property: {
    id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    address: "109 Waiko Rd",
    city: "Wailuku",
    state: "HI",
    country: "US",
    latitude: 20.8899,
    longitude: -156.4925,
    property_type: "Land",
    listing_type: "Land for auction",
    description:
      "Flexible fully graded development site with strong visibility and utility access. The parcel offers level topography suitable for commercial or industrial build-out subject to local zoning. Proximity to major corridors supports logistics and last-mile distribution. Environmental and utility studies are available upon request. Ideal for investors or developers seeking a scalable footprint in a growing market.",
    size_sqft: 435_600,
    price: 2_650_000,
    rent: 11_042,
    clear_height: null,
    loading_docks: null,
    image: IMG[0] ?? null,
  },
  images: [...IMG],
};
