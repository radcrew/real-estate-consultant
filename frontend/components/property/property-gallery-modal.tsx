"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { NcModal } from "@components/ui/nc-modal";
import { ImagePlaceholder } from "./image-placeholder";

type PropertyGalleryModalProps = {
  images: string[];
  alt: string;
  isOpen: boolean;
  initialIndex?: number;
  onClose: () => void;
};

export const PropertyGalleryModal = ({
  images,
  alt,
  isOpen,
  initialIndex = 0,
  onClose,
}: PropertyGalleryModalProps) => {
  const [current, setCurrent] = useState(initialIndex);
  const [failedIndexes, setFailedIndexes] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isOpen) {
      setCurrent(initialIndex);
      setFailedIndexes(new Set());
    }
  }, [isOpen, initialIndex]);

  const prev = () => setCurrent((c) => (c - 1 + images.length) % images.length);
  const next = () => setCurrent((c) => (c + 1) % images.length);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") prev();
      if (e.key === "ArrowRight") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, images.length]);

  const markFailed = (i: number) =>
    setFailedIndexes((prev) => new Set(prev).add(i));

  return (
    <NcModal
      isOpenProp={isOpen}
      onCloseModal={onClose}
      modalTitle={`${current + 1} / ${images.length}`}
      contentExtraClass="max-w-5xl"
      contentPaddingClass="p-0"
      renderTrigger={() => null}
      renderContent={() => (
        <div className="flex flex-col">
          {/* Main image */}
          <div className="relative aspect-[16/10] w-full overflow-hidden bg-neutral-100 dark:bg-neutral-900">
            {failedIndexes.has(current) ? (
              <ImagePlaceholder label={alt} />
            ) : (
              <Image
                key={current}
                src={images[current]}
                alt={`${alt} — photo ${current + 1}`}
                fill
                sizes="(max-width: 1024px) 100vw, 1024px"
                className="object-contain"
                priority
                onError={() => markFailed(current)}
              />
            )}

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

          {/* Thumbnail strip */}
          {images.length > 1 && (
            <div className="flex gap-2 overflow-x-auto px-4 py-3">
              {images.map((src, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setCurrent(i)}
                  className={`relative h-14 w-20 shrink-0 overflow-hidden rounded-lg border-2 transition-colors ${
                    i === current
                      ? "border-primary-600"
                      : "border-transparent opacity-60 hover:opacity-100"
                  }`}
                  aria-label={`Go to photo ${i + 1}`}
                >
                  {failedIndexes.has(i) ? (
                    <ImagePlaceholder />
                  ) : (
                    <Image
                      src={src}
                      alt={`${alt} thumbnail ${i + 1}`}
                      fill
                      sizes="80px"
                      className="object-cover"
                      onError={() => markFailed(i)}
                    />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    />
  );
};
