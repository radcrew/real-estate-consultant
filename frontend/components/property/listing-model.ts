import type { ListingDetailResponse } from "@services/listings";
import type { SearchProperty, SearchPropertyMatch } from "@services/search";
import type { PropertyBroker, PropertyModel, PropertySpec } from "@typings/property";
import { formatInteger } from "@utils/common";
import { mapsHref } from "@utils/listings/maps";
import { mapSearchPropertyMatchToListing } from "@utils/search/property";

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
const toPropertyModel = (
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

