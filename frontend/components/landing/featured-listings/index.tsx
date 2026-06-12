"use client";

import { useEffect, useState } from "react";

import { brand } from "@config/brand";
import { detailToModel, type PropertyModel } from "@components/property/listing-model";
import { PropertyCard, PropertyCardSkeleton, PROPERTY_GRID } from "@components/property/property-card";
import { ButtonSecondary } from "@components/ui/button-secondary";
import { Heading2 } from "@components/ui/heading2";
import { listingsService } from "@services/listings";

const HEADING = brand.sections.featured.heading;
const SUB_HEADING = (
  <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
    {brand.sections.featured.subHeading}
  </span>
);
export const FeaturedListings = () => {
  const [models, setModels] = useState<PropertyModel[] | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listingsService
      .getFeaturedListings({ signal: controller.signal })
      .then((res) => setModels(res.listings.map(detailToModel)))
      .catch(() => setModels([]));
    return () => controller.abort();
  }, []);

  const loading = models === null;

  return (
    <section className="relative">
      <Heading2 heading={HEADING} subHeading={SUB_HEADING} />

      <div className={PROPERTY_GRID}>
        {loading
          ? Array.from({ length: 6 }).map((_, i) => <PropertyCardSkeleton key={i} />)
          : models.map((item) => <PropertyCard key={item.id} data={item} />)}
      </div>

      <div className="mt-14 flex justify-center">
        <ButtonSecondary href="/listings">Browse all properties</ButtonSecondary>
      </div>
    </section>
  );
};
