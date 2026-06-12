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
  const [current, setCurrent] = useState(0);
  const [failedIndexes, setFailedIndexes] = useState<Set<number>>(new Set());
  const markFailed = (i: number) =>
    setFailedIndexes((prev) => new Set(prev).add(i));

  const [emblaRef, emblaApi] = useEmblaCarousel({ loop: true });

  useEffect(() => {
    if (!emblaApi) return;
    const onSelect = () => setCurrent(emblaApi.selectedScrollSnap());
    emblaApi.on("select", onSelect);
    return () => { emblaApi.off("select", onSelect); };
  }, [emblaApi]);

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
    <div className={cn("relative overflow-hidden rounded-2xl bg-neutral-100 dark:bg-neutral-900", className)}>
      {/* Carousel */}
      <div
        ref={emblaRef}
        className="overflow-hidden cursor-grab active:cursor-grabbing"
      >
        <div className="flex">
          {images.map((src, i) => (
            <div key={i} className="relative flex min-w-0 flex-[0_0_100%] items-center justify-center">
              {failedIndexes.has(i) ? (
                <div className="relative aspect-[4/3] w-full">
                  <ImagePlaceholder label={alt !== "Listing photo" ? alt : undefined} />
                </div>
              ) : (
                <Image
                  src={src}
                  alt={`${alt} ${i + 1}`}
                  width={1200}
                  height={900}
                  className="max-h-[520px] w-auto object-contain"
                  priority={i === 0}
                  onError={() => markFailed(i)}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Prev / Next */}
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

          {/* Counter */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-3 py-1 text-xs font-medium text-white">
            {current + 1} / {images.length}
          </div>
        </>
      )}
    </div>
  );
};
