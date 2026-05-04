import type { SearchPropertyMatch } from "@services/search";

const PLACEHOLDER_IMAGE =
  "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=900&h=560&q=80";

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
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(sqft)} SF`;
};

const formatMoney = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);

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
  const { property: p, match_score } = row;
  const id = p.id?.trim() || `match-${index}`;
  const title = titleFromProperty(p);

  return {
    id,
    category: p.property_type?.trim() || "Property",
    transactionType: p.listing_type?.trim() || "—",
    title,
    location: locationFromProperty(p),
    sqftLabel: formatSqft(p.size_sqft),
    priceLabel: priceLabelFromProperty(p),
    imageSrc: PLACEHOLDER_IMAGE,
    imageAlt: title,
    matchScore: Math.round(match_score),
    matchBlurb: blurbFromProperty(p),
  };
};

export const mapSearchPropertyMatchesToListings = (rows: SearchPropertyMatch[]): ResultCardListing[] =>
  rows.map(mapSearchPropertyMatchToListing);
