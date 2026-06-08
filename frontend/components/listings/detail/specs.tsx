import type { ReactNode } from "react";
import { Building2, Maximize, MoveVertical, Tag, Truck } from "lucide-react";

import type { ListingProperty } from "@services/listings";
import { formatFeet, formatSqft } from "@utils/common";

/**
 * Voyager-style "amenities" section adapted for CRE: a card with an icon grid
 * of the property's key building specifications. Renders only the specs the
 * listing actually carries, and nothing if there are none.
 */
type ListingSpecsSectionProps = {
  property: ListingProperty;
};

type Spec = { icon: ReactNode; label: string; value: string };

export const ListingSpecsSection = ({ property: p }: ListingSpecsSectionProps) => {
  const specs: Spec[] = [];

  const propertyType = p.property_type?.trim();
  if (propertyType) {
    specs.push({ icon: <Building2 className="size-5" aria-hidden />, label: "Property type", value: propertyType });
  }

  const listingType = p.listing_type?.trim();
  if (listingType) {
    specs.push({ icon: <Tag className="size-5" aria-hidden />, label: "Listing type", value: listingType });
  }

  const size = formatSqft(p.size_sqft);
  if (size) {
    specs.push({ icon: <Maximize className="size-5" aria-hidden />, label: "Building size", value: size });
  }

  const clearHeight = formatFeet(p.clear_height);
  if (clearHeight) {
    specs.push({ icon: <MoveVertical className="size-5" aria-hidden />, label: "Clear height", value: clearHeight });
  }

  if (p.loading_docks != null) {
    specs.push({ icon: <Truck className="size-5" aria-hidden />, label: "Loading docks", value: String(p.loading_docks) });
  }

  if (specs.length === 0) {
    return null;
  }

  return (
    <section
      className="mt-10 rounded-2xl border border-neutral-200 p-6 sm:p-8 dark:border-neutral-700"
      aria-labelledby="listing-specs"
    >
      <h2
        id="listing-specs"
        className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100"
      >
        Property specifications
      </h2>
      <p className="mt-1 text-neutral-500 dark:text-neutral-400">
        Key building details for this property.
      </p>
      <div className="my-5 w-14 border-b border-neutral-200 dark:border-neutral-700" />
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {specs.map((spec) => (
          <div key={spec.label} className="flex items-center gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600 dark:bg-primary-500/10 dark:text-primary-400">
              {spec.icon}
            </div>
            <div className="min-w-0">
              <p className="text-sm text-neutral-500 dark:text-neutral-400">{spec.label}</p>
              <p className="truncate font-medium text-neutral-900 dark:text-neutral-100">
                {spec.value}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
