import type { ResultCardListing } from "@utils/search/property";

export interface PropertySpec {
  label: string;
  value: string;
}

export interface PropertyBroker {
  name: string | null;
  email: string | null;
  phone: string | null;
}

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
export interface PropertyModel extends ResultCardListing {
  href: string;
  description: string | null;
  galleryImgs: string[];
  specs: PropertySpec[];
  map: { lat: number; lng: number } | null;
  mapsHref: string | null;
  broker: PropertyBroker;
}
