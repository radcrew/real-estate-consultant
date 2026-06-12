"use client";

import { useEffect, useState } from "react";

import { brand } from "@config/brand";
import { detailToModel } from "@components/property/listing-model";
import { SectionGridFeatureProperty } from "@components/property/section-grid-feature-property";
import { PropertyCardSkeleton, PROPERTY_GRID } from "@components/property/property-card";
import { listingsService } from "@services/listings";
import type { PropertyModel } from "@components/property/listing-model";

export const FeaturedListings = () => {
  const [models, setModels] = useState<PropertyModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    listingsService
      .getFeaturedListings({ signal: controller.signal })
      .then((res) => setModels(res.listings.map(detailToModel)))
      .catch(() => {/* silently hide the section on error */})
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  if (loading) {
    return (
      <div className={`${PROPERTY_GRID} px-4 py-8`}>
        {Array.from({ length: 6 }).map((_, i) => (
          <PropertyCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!models.length) return null;

  return (
    <SectionGridFeatureProperty
      className="relative"
      heading={brand.sections.featured.heading}
      subHeading={
        <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
          {brand.sections.featured.subHeading}
        </span>
      }
      data={models}
      cta={{ label: "Browse all properties", href: "/listings" }}
    />
  );
};
