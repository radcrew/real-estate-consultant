"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";
import useEmblaCarousel from "embla-carousel-react";

import { cn } from "@utils/common";
import { ImagePlaceholder } from "./image-placeholder";

export interface PropertyGalleryProps {
  images: string[];
  alt?: string;
  className?: string;
}

export const PropertyGallery = ({
  images,
  alt = "Listing photo",
  className,
}: PropertyGalleryProps) => {
  const [failedIndexes, setFailedIndexes] = useState<Set<number>>(new Set());
  const markFailed = (i: number) =>
    setFailedIndexes((prev) => new Set(prev).add(i));

  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: true,
    dragFree: true,
    align: "start",
  });

  const prev = useCallback(() => emblaApi?.scrollPrev(), [emblaApi]);
  const next = useCallback(() => emblaApi?.scrollNext(), [emblaApi]);

  if (!images.length) {
    return (
      <div className={cn("relative aspect-[4/3] w-full overflow-hidden rounded-2xl", className)}>
        <ImagePlaceholder label={alt !== "Listing photo" ? alt : undefined} />
      </div>
    );
  }

  return (
    <div className={cn("group relative overflow-hidden rounded-2xl bg-neutral-100 dark:bg-neutral-900", className)}>
      <div ref={emblaRef} className="overflow-hidden cursor-grab active:cursor-grabbing">
        <div className="flex gap-2 p-2">
          {images.map((src, i) => (
            <div key={i} className="relative h-80 w-[569px] shrink-0 overflow-hidden rounded-xl">
              {failedIndexes.has(i) ? (
                <ImagePlaceholder label={alt !== "Listing photo" ? alt : undefined} />
              ) : (
                <Image
                  src={src}
                  alt={`${alt} ${i + 1}`}
                  fill
                  className="object-cover"
                  sizes="569px"
                  priority={i === 0}
                  onError={() => markFailed(i)}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {images.length > 1 && (
        <>
          <button
            type="button"
            onClick={prev}
            className="absolute left-3 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow-md hover:bg-white dark:bg-neutral-800/80 dark:hover:bg-neutral-800"
            aria-label="Previous photo"
          >
            <ChevronLeft className="h-5 w-5 text-neutral-700 dark:text-neutral-200" />
          </button>
          <button
            type="button"
            onClick={next}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full bg-white/80 p-2 shadow-md hover:bg-white dark:bg-neutral-800/80 dark:hover:bg-neutral-800"
            aria-label="Next photo"
          >
            <ChevronRight className="h-5 w-5 text-neutral-700 dark:text-neutral-200" />
          </button>
        </>
      )}
    </div>
  );
};
