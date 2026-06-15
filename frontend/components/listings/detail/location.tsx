import type { PropertyModel } from "@typings/property";
import { PropertyMap } from "@components/property/property-map";

/**
 * Voyager-style "Location" section card for the listing detail: heading +
 * address + an embedded map centered on the listing. Renders only when the
 * listing has coordinates.
 */
type ListingLocationSectionProps = {
  model: PropertyModel;
};

export const ListingLocationSection = ({ model }: ListingLocationSectionProps) => {
  if (!model.map) {
    return null;
  }

  return (
    <section
      className="mt-10 rounded-2xl border border-neutral-200 p-6 sm:p-8 dark:border-neutral-700"
      aria-labelledby="listing-location"
    >
      <h2
        id="listing-location"
        className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100"
      >
        Location
      </h2>
      {model.location ? (
        <p className="mt-1 text-neutral-500 dark:text-neutral-400">{model.location}</p>
      ) : null}
      <div className="my-5 w-14 border-b border-neutral-200 dark:border-neutral-700" />
      <PropertyMap items={[model]} defaultZoom={14} className="h-72 sm:h-96" />
    </section>
  );
};
