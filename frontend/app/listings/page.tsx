"use client";

import { useEffect, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { detailToModel, type PropertyModel } from "@components/property/listing-model";
import { PropertyCardSkeleton, PROPERTY_GRID } from "@components/property/property-card";
import { SectionGridFeatureProperty } from "@components/property/section-grid-feature-property";
import { brand } from "@config/brand";
import { listingsService } from "@services/listings";

const ListingsIndexPage = () => {
  const [models, setModels] = useState<PropertyModel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    listingsService
      .getFeaturedListings({ signal: controller.signal })
      .then((res) => setModels(res.listings.map(detailToModel)))
      .catch(() => {})
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      <div className="flex flex-col items-start gap-6 border-b border-neutral-200 pb-12 lg:flex-row lg:items-end lg:justify-between dark:border-neutral-700">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
            {brand.sections.listings.heading}
          </h1>
          <p className="mt-3 text-base text-neutral-500 md:text-lg dark:text-neutral-400">
            {brand.sections.listings.subHeading} Start an AI-guided search to see properties
            matched to your needs.
          </p>
        </div>
        <ButtonPrimary href="/questionnaire" sizeClass="px-7 py-3.5" fontSize="text-base font-medium">
          Start searching
        </ButtonPrimary>
      </div>

      {loading ? (
        <div className={`${PROPERTY_GRID} pt-12`}>
          {Array.from({ length: 6 }).map((_, i) => (
            <PropertyCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <SectionGridFeatureProperty
          className="pt-12"
          heading={brand.sections.featured.heading}
          subHeading={
            <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
              {brand.sections.featured.subHeading}
            </span>
          }
          data={models}
        />
      )}
    </div>
  );
};

export default ListingsIndexPage;
