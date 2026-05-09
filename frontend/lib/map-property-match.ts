import { formatInteger, formatMoney } from "@utils/common";
import type { SearchPropertyMatch } from "@services/search";

export type ResultCardListing = {
  id: string;
  category: string;
  transactionType: string;
  title: string;
  location: string;
  sqftLabel: string;
  priceLabel: string | null;
  imageSrc: string;
  imageAlt: string;
  matchScore: number;
  matchBlurb: string;
};

const formatSqft = (sqft: number | null): string => {
  if (sqft == null || Number.isNaN(sqft)) {
    return "—";
  }
  return `${formatInteger(sqft)} SF`;
};

const priceLabelFromProperty = (p: SearchPropertyMatch["property"]): string | null => {
  const sale = p.price != null && !Number.isNaN(p.price) ? formatMoney(p.price) : null;
  const lease = p.rent != null && !Number.isNaN(p.rent) ? `${formatMoney(p.rent)}/yr` : null;
  if (sale && lease) {
    return `${sale} · ${lease} rent`;
  }
  return sale ?? lease;
};

const titleFromProperty = (p: SearchPropertyMatch["property"]): string => {
  if (p.address?.trim()) {
    return p.address.trim();
  }
  const parts = [p.city, p.state].filter(Boolean);
  if (parts.length) {
    return parts.join(", ");
  }
  return p.property_type?.trim() || "Property";
};

const locationFromProperty = (p: SearchPropertyMatch["property"]): string => {
  const parts = [p.city, p.state, p.country].filter((x) => x && String(x).trim());
  if (parts.length) {
    return parts.join(" · ");
  }
  return p.address?.trim() || "Location not specified";
};

const blurbFromProperty = (p: SearchPropertyMatch["property"]): string => {
  const d = p.description?.trim();
  if (!d) {
    return "Matched from your search profile.";
  }
  return d.length <= 160 ? d : `${d.slice(0, 157)}…`;
};

export const mapSearchPropertyMatchToListing = (
  row: SearchPropertyMatch,
  index: number,
): ResultCardListing => {
  const { property, match_score } = row;
  const id = property.id?.trim() || `match-${index}`;
  const title = titleFromProperty(property);

  return {
    id,
    category: property.property_type?.trim() || "Property",
    transactionType: property.listing_type?.trim() || "—",
    title,
    location: locationFromProperty(property),
    sqftLabel: formatSqft(property.size_sqft),
    priceLabel: priceLabelFromProperty(property),
    imageSrc: property.image || "",
    imageAlt: title,
    matchScore: Math.round(match_score),
    matchBlurb: blurbFromProperty(property),
  };
};

export const mapSearchPropertyMatchesToListings = (rows: SearchPropertyMatch[]): ResultCardListing[] =>
  rows.map(mapSearchPropertyMatchToListing);
