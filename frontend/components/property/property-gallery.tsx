"use client";

import { useState } from "react";
import Image from "next/image";
import { Images } from "lucide-react";

import { cn } from "@utils/common";

import { ImagePlaceholder } from "./image-placeholder";
import { PropertyGalleryModal } from "./property-gallery-modal";

/**
 * Voyager-style listing gallery — one large cover plus a 2x2 thumbnail grid.
 * Clicking any tile (or "Show all photos") opens a full-screen photo modal
 * (`PropertyGalleryModal`). Falls back to a placeholder when there are no images.
 */
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
  const [open, setOpen] = useState(false);
  const [initialIndex, setInitialIndex] = useState(0);
  const [failedIndexes, setFailedIndexes] = useState<Set<number>>(new Set());
  const markFailed = (i: number) =>
    setFailedIndexes((prev) => new Set(prev).add(i));

  if (!images.length) {
    return (
      <div
        className={cn(
          "relative aspect-[16/9] w-full overflow-hidden rounded-2xl",
          className,
        )}
      >
        <ImagePlaceholder label={alt !== "Listing photo" ? alt : undefined} />
      </div>
    );
  }

  const [cover, ...rest] = images;
  const thumbs = rest.slice(0, 4);
  const openModal = (index = 0) => { setInitialIndex(index); setOpen(true); };

  return (
    <div className={cn("relative", className)}>
      <div className="grid h-80 grid-cols-2 grid-rows-2 gap-1 overflow-hidden rounded-2xl sm:h-[460px] sm:grid-cols-4 sm:gap-2">
        <button
          type="button"
          onClick={() => openModal(0)}
          aria-label="Open photo gallery"
          className="group relative col-span-2 row-span-2 cursor-pointer focus:outline-none"
        >
          {failedIndexes.has(0) ? (
            <ImagePlaceholder label={alt !== "Listing photo" ? alt : undefined} />
          ) : (
            <Image
              src={cover}
              alt={alt}
              fill
              priority
              sizes="(max-width: 640px) 100vw, 50vw"
              className="object-cover transition-opacity group-hover:opacity-90"
              onError={() => markFailed(0)}
            />
          )}
        </button>
        {thumbs.map((img, index) => (
          <button
            type="button"
            key={index}
            onClick={() => openModal(index + 1)}
            aria-label="Open photo gallery"
            className="group relative hidden cursor-pointer focus:outline-none sm:block"
          >
            {failedIndexes.has(index + 1) ? (
              <ImagePlaceholder />
            ) : (
              <Image
                src={img}
                alt={alt}
                fill
                sizes="25vw"
                className="object-cover transition-opacity group-hover:opacity-90"
                onError={() => markFailed(index + 1)}
              />
            )}
          </button>
        ))}
      </div>

      {images.length > 1 && (
        <button
          type="button"
          onClick={() => openModal(0)}
          className="absolute right-3 bottom-3 inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-neutral-700 shadow-md hover:bg-neutral-100 focus:outline-none dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800"
        >
          <Images className="h-4 w-4" aria-hidden />
          Show all photos
        </button>
      )}

      <PropertyGalleryModal
        images={images}
        alt={alt}
        isOpen={open}
        initialIndex={initialIndex}
        onClose={() => setOpen(false)}
      />
    </div>
  );
};
