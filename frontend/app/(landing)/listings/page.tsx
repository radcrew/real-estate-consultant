"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

import { ButtonPrimary } from "@components/ui/button-primary";
import { detailToModel } from "@components/property/listing-model";
import type { PropertyModel } from "@typings/property";
import { PropertyCard, PropertyCardSkeleton, PROPERTY_GRID } from "@components/property/card";
import { Heading2 } from "@components/ui/heading2";
import { brand } from "@config/brand";
import { listingsService } from "@services/listings";

const isCancellation = (err: unknown) =>
  (err instanceof DOMException && err.name === "AbortError") ||
  (err != null && typeof err === "object" && "code" in err && (err as { code: string }).code === "ERR_CANCELED");

const ListingsIndexPage = () => {
  const pathname = usePathname();
  const [models, setModels] = useState<PropertyModel[] | null>(null);

  useEffect(() => {
    setModels(null);
    const controller = new AbortController();
    listingsService
      .getFeaturedListings({ signal: controller.signal })
      .then((res) => setModels(res.listings.map(detailToModel)))
      .catch((err: unknown) => { if (!isCancellation(err)) setModels([]); });
    return () => controller.abort();
  }, [pathname]);

  const loading = models === null;

  return (
    <div className="mx-auto w-full max-w-screen-xl px-4 py-16 lg:py-20 2xl:max-w-screen-2xl 2xl:px-32">
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

      <section className="relative pt-12">
        <Heading2
          heading={brand.sections.featured.heading}
          subHeading={
            <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
              {brand.sections.featured.subHeading}
            </span>
          }
        />
        <div className={PROPERTY_GRID}>
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <PropertyCardSkeleton key={i} />)
            : models.map((item) => <PropertyCard key={item.id} data={item} />)}
        </div>
      </section>
    </div>
  );
};

export default ListingsIndexPage;
