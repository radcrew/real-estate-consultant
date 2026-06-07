"use client";

import { useState } from "react";
import Image from "next/image";
import { Building2, Images } from "lucide-react";

import { cn } from "@utils/common";

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

  if (!images.length) {
    return (
      <div
        className={cn(
          "flex aspect-[16/9] w-full items-center justify-center rounded-2xl bg-neutral-100 text-neutral-300 dark:bg-neutral-800 dark:text-neutral-600",
          className,
        )}
      >
        <Building2 className="h-12 w-12" aria-hidden />
      </div>
    );
  }

  const [cover, ...rest] = images;
  const thumbs = rest.slice(0, 4);
  const openModal = () => setOpen(true);

  return (
    <div className={cn("relative", className)}>
      <div className="grid h-80 grid-cols-2 grid-rows-2 gap-1 overflow-hidden rounded-2xl sm:h-[460px] sm:grid-cols-4 sm:gap-2">
        <button
          type="button"
          onClick={openModal}
          aria-label="Open photo gallery"
          className="group relative col-span-2 row-span-2 cursor-pointer focus:outline-none"
        >
          <Image
            src={cover}
            alt={alt}
            fill
            priority
            sizes="(max-width: 640px) 100vw, 50vw"
            className="object-cover transition-opacity group-hover:opacity-90"
          />
        </button>
        {thumbs.map((img, index) => (
          <button
            type="button"
            key={index}
            onClick={openModal}
            aria-label="Open photo gallery"
            className="group relative hidden cursor-pointer focus:outline-none sm:block"
          >
            <Image
              src={img}
              alt={alt}
              fill
              sizes="25vw"
              className="object-cover transition-opacity group-hover:opacity-90"
            />
          </button>
        ))}
      </div>

      {images.length > 1 && (
        <button
          type="button"
          onClick={openModal}
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
        onClose={() => setOpen(false)}
      />
    </div>
  );
};

export default PropertyGallery;
