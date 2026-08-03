"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { detailToModel } from "@components/property/listing-model";
import type { PropertyModel } from "@typings/property";
import { PropertyCard, PropertyCardSkeleton, PROPERTY_GRID } from "@components/property/card";
import { Heading2 } from "@components/ui/heading2";
import { brand } from "@config/brand";
import { listingsService } from "@services/listings";
import { PAGE_CONTAINER } from "@components/ui/styles";
import { cn } from "@utils/common";

const isCancellation = (err: unknown) =>
  (err instanceof DOMException && err.name === "AbortError") ||
  (err != null && typeof err === "object" && "code" in err && (err as { code: string }).code === "ERR_CANCELED");

export type ListingsIndexViewProps = {
  /**
   * Rendered inside the account shell rather than as the `/listings` page. The
   * shell already supplies the page container, width cap and vertical rhythm,
   * so the standalone spacing would stack on top of it.
   */
  embedded?: boolean;
  /**
   * Shown as a back affordance when the view is reached from somewhere that
   * can return to it — the account Saved tab's empty state, today. Without it
   * an embedded view is a one-way trip out of whatever opened it.
   */
  onBack?: () => void;
};

/**
 * The `/listings` index: intro + "Start searching" CTA over the featured grid.
 *
 * Extracted from the route so the account shell can render it in-panel — the
 * Saved tab's empty state sends users here, and navigating to the real route
 * would drop the account sidebar mid-flow.
 */
export const ListingsIndexView = ({ embedded = false, onBack }: ListingsIndexViewProps) => {
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
    <div className={embedded ? undefined : cn(PAGE_CONTAINER, "py-16 lg:py-20")}>
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="mb-6 inline-flex cursor-pointer items-center gap-2 text-sm font-medium text-neutral-500 transition-colors hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
        >
          <ArrowLeft className="size-4" aria-hidden />
          Back to saved properties
        </button>
      ) : null}

      <div className="flex flex-col items-start gap-6 border-b border-neutral-200 pb-12 lg:flex-row lg:items-end lg:justify-between dark:border-neutral-700">
        <div className="max-w-2xl">
          <h1
            className={cn(
              "font-semibold text-neutral-900 dark:text-neutral-100",
              embedded ? "text-2xl" : "text-3xl md:text-4xl",
            )}
          >
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
