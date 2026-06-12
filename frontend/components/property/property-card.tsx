import Image from "next/image";
import Link from "next/link";
import { MapPin } from "lucide-react";

import { Badge } from "@components/ui/badge";
import { BtnLikeIcon } from "@components/ui/btn-like-icon";
import type { PropertyModel } from "@components/property/listing-model";
import { ImagePlaceholder } from "@components/property/image-placeholder";
import { cn } from "@utils/common";

/**
 * Voyager-style property card, ported from Voyager's `StayCard` but driven by the
 * real `PropertyModel` (CRE spec chips + price instead of beds/reviews). Single
 * card used by the home grid, listings grid, and map view. Falls back to a
 * placeholder when a listing has no image, and shows a match-score badge when
 * the model carries one (search results).
 */
/** Responsive 3-up grid that PropertyCard / PropertyCardSkeleton render into. */
export const PROPERTY_GRID =
  "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3";

/** Loading placeholder mirroring PropertyCard's shape. */
export const PropertyCardSkeleton = () => (
  <div className="overflow-hidden rounded-2xl border border-neutral-100 dark:border-neutral-800">
    <div className="aspect-[4/3] animate-pulse bg-neutral-100 dark:bg-neutral-800" />
    <div className="space-y-3 p-4">
      <div className="h-4 w-1/3 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
      <div className="h-5 w-4/5 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
      <div className="h-4 w-2/3 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
    </div>
  </div>
);

export interface PropertyCardProps {
  data: PropertyModel;
  className?: string;
}

const transactionColor = (transactionType: string) =>
  transactionType.toLowerCase().includes("sale") ? "green" : "blue";

export const PropertyCard = ({ data, className }: PropertyCardProps) => {
  const cover = data.galleryImgs[0] || data.imageSrc;
  const hasTransaction = data.transactionType && data.transactionType !== "—";

  return (
    <Link
      href={data.href}
      className={cn(
        "group relative flex flex-col overflow-hidden rounded-2xl border border-neutral-100 bg-white transition-shadow hover:shadow-xl dark:border-neutral-800 dark:bg-neutral-900",
        className,
      )}
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-neutral-100 dark:bg-neutral-800">
        {cover ? (
          <Image
            src={cover}
            alt={data.imageAlt}
            fill
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <ImagePlaceholder label={data.title} />
        )}

        <div className="absolute left-3 top-3 flex flex-col items-start gap-2">
          {hasTransaction && (
            <Badge
              name={data.transactionType}
              color={transactionColor(data.transactionType)}
            />
          )}
          {data.matchScore > 0 && (
            <Badge name={`${data.matchScore}% match`} color="green" />
          )}
        </div>

        <BtnLikeIcon id={data.id} className="absolute right-3 top-3" />
      </div>

      <div className="flex flex-1 flex-col space-y-3 p-4">
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          {data.category}
        </span>
        <h2 className="text-base font-semibold text-neutral-900 dark:text-white">
          <span className="line-clamp-1">{data.title}</span>
        </h2>
        <div className="flex items-center space-x-1.5 text-sm text-neutral-500 dark:text-neutral-400">
          <MapPin className="h-4 w-4 shrink-0" aria-hidden />
          <span className="line-clamp-1">{data.location}</span>
        </div>

        {data.specs.length > 0 && (
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-neutral-600 dark:text-neutral-300">
            {data.specs.map((spec) => (
              <span key={spec.label}>
                <span className="text-neutral-400 dark:text-neutral-500">
                  {spec.label}:{" "}
                </span>
                {spec.value}
              </span>
            ))}
          </div>
        )}

        <div className="w-14 border-b border-neutral-100 dark:border-neutral-800" />
        <div className="mt-auto flex items-center justify-between">
          <span className="text-base font-semibold text-neutral-900 dark:text-white">
            {data.priceLabel ?? "Price on request"}
          </span>
        </div>
      </div>
    </Link>
  );
};
