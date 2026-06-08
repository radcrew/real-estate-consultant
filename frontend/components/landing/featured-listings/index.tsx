import { brand } from "@config/brand";
import { FEATURED_LISTINGS } from "@constants";
import { featuredToModel } from "@components/property/listing-model";
import { SectionGridFeatureProperty } from "@components/property/section-grid-feature-property";

const FEATURED_MODELS = FEATURED_LISTINGS.map(featuredToModel);

export const FeaturedListings = () => (
  <SectionGridFeatureProperty
    className="relative"
    heading={brand.sections.featured.heading}
    subHeading={
      <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
        {brand.sections.featured.subHeading}
      </span>
    }
    data={FEATURED_MODELS}
    cta={{ label: "Browse all properties", href: "/listings" }}
  />
);
