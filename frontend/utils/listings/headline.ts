import type { ListingProperty } from "@services/listings";

export function listingTitle(p: ListingProperty): string {
  const fromAddress = p.address?.trim();
  if (fromAddress) {
    return fromAddress;
  }
  const cityState = [p.city, p.state].filter(Boolean).join(", ");
  return cityState || "Property listing";
}

export function listingLocationLine(p: ListingProperty): string | null {
  const line = [p.city, p.state, p.country].filter(Boolean).join(", ");
  return line || null;
}
