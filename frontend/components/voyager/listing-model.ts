import type { FeaturedListing } from "@constants";
import type { ListingDetailResponse } from "@services/listings";
import type { SearchProperty, SearchPropertyMatch } from "@services/search";
import { formatInteger } from "@utils/common";
import { mapsHref } from "@utils/listings/maps";
import {
  mapSearchPropertyMatchToListing,
  type ResultCardListing,
} from "@utils/search/property";

/**
 * Voyager listing view-model.
 *
 * The bridge between the real backend data (`SearchProperty` /
 * `ListingDetailResponse`) and the Voyager-style components — it replaces
 * Voyager's demo `StayDataType`. It REUSES the existing
 * `mapSearchPropertyMatchToListing` for the shared card fields (title, location,
 * category, price/sqft labels, match score) so there's one source of truth, and
 * adds the extras Voyager's cards/map/detail need: href, gallery, CRE spec
 * chips, map coordinates, and broker contact.
 */
export interface PropertySpec {
  label: string;
  value: string;
}

export interface PropertyBroker {
  name: string | null;
  email: string | null;
  phone: string | null;
}

export interface PropertyModel extends ResultCardListing {
  href: string;
  description: string | null;
  galleryImgs: string[];
  specs: PropertySpec[];
  map: { lat: number; lng: number } | null;
  mapsHref: string | null;
  broker: PropertyBroker;
}

const isNum = (v: number | null | undefined): v is number =>
  v != null && !Number.isNaN(v);

const buildSpecs = (p: SearchProperty): PropertySpec[] => {
  const specs: PropertySpec[] = [];
  if (isNum(p.size_sqft)) {
    specs.push({ label: "Size", value: `${formatInteger(p.size_sqft)} SF` });
  }
  if (isNum(p.clear_height)) {
    specs.push({
      label: "Clear height",
      value: `${formatInteger(p.clear_height)} ft`,
    });
  }
  if (isNum(p.loading_docks)) {
    specs.push({ label: "Loading docks", value: formatInteger(p.loading_docks) });
  }
  return specs;
};

const buildBroker = (p: SearchProperty): PropertyBroker => ({
  name: p.listing_broker_name?.trim() || null,
  email: p.listing_broker_email?.trim() || null,
  phone: p.listing_broker_phone?.trim() || null,
});

const buildMap = (p: SearchProperty) =>
  isNum(p.latitude) && isNum(p.longitude)
    ? { lat: p.latitude, lng: p.longitude }
    : null;

/** Map a scored search result to the Voyager view-model. */
export const toPropertyModel = (
  match: SearchPropertyMatch,
  index = 0,
): PropertyModel => {
  const base = mapSearchPropertyMatchToListing(match, index);
  const p = match.property;
  return {
    ...base,
    href: `/listings/${base.id}`,
    description: p.description?.trim() || null,
    galleryImgs: p.image ? [p.image] : [],
    specs: buildSpecs(p),
    map: buildMap(p),
    mapsHref: mapsHref(p.latitude, p.longitude),
    broker: buildBroker(p),
  };
};

export const toPropertyModels = (
  rows: SearchPropertyMatch[],
): PropertyModel[] => rows.map((row, index) => toPropertyModel(row, index));

/** Map a bare property (no match score) to the view-model. */
export const propertyToModel = (
  property: SearchProperty,
  index = 0,
): PropertyModel => toPropertyModel({ property, match_score: 0 }, index);

/** Map a listing-detail response, using its full image set as the gallery. */
export const detailToModel = (detail: ListingDetailResponse): PropertyModel => {
  const model = propertyToModel(detail.property);
  return {
    ...model,
    galleryImgs: detail.images?.length ? detail.images : model.galleryImgs,
  };
};

/**
 * Map a curated `FeaturedListing` (static home data) to the view-model, so the
 * home grid renders through the same `PropertyCard` as live results. CRE specs
 * beyond size aren't part of the curated data, so only the size chip is built.
 */
export const featuredToModel = (listing: FeaturedListing): PropertyModel => ({
  id: listing.id,
  category: listing.category,
  transactionType: listing.transactionType,
  title: listing.title,
  location: listing.location,
  sqftLabel: listing.sqftLabel,
  priceLabel: listing.priceLabel,
  imageSrc: listing.imageSrc,
  imageAlt: listing.imageAlt,
  matchScore: 0,
  matchBlurb: "",
  href: `/listings/${listing.id}`,
  description: null,
  galleryImgs: listing.imageSrc ? [listing.imageSrc] : [],
  specs: [{ label: "Size", value: listing.sqftLabel }],
  map: null,
  mapsHref: null,
  broker: { name: null, email: null, phone: null },
});
