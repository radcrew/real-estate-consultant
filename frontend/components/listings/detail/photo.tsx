"use client";

import Image from "next/image";
import type { KeyboardEvent } from "react";
import { useCallback, useEffect } from "react";
import useEmblaCarousel from "embla-carousel-react";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@components/ui/button";

const TILE =
  "relative min-w-0 flex-[0_0_auto] aspect-[4/3] w-[calc((100%-0.5rem)/2)] overflow-hidden rounded-md bg-muted";

type ListingPhotoCarouselProps = {
  gallery: string[];
  imageTitle: string;
};

export const ListingPhotoCarousel = ({ gallery, imageTitle }: ListingPhotoCarouselProps) => {
  const canLoop = gallery.length > 1;
  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: canLoop,
    align: "start",
    dragFree: false,
    slidesToScroll: 1,
  });

  useEffect(() => {
    emblaApi?.reInit();
  }, [emblaApi, gallery]);

  const scrollPrev = useCallback(() => {
    emblaApi?.scrollPrev();
  }, [emblaApi]);

  const scrollNext = useCallback(() => {
    emblaApi?.scrollNext();
  }, [emblaApi]);

  const onViewportKeyDown = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (!canLoop) {
        return;
      }
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        scrollPrev();
      }
      if (e.key === "ArrowRight") {
        e.preventDefault();
        scrollNext();
      }
    },
    [canLoop, scrollPrev, scrollNext],
  );

  return (
    <div className="w-full overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="relative bg-muted/40 p-3 sm:p-4">
        {gallery.length === 0 ? (
          <div className="flex min-h-[200px] items-center justify-center text-sm text-muted-foreground">
            No photos
          </div>
        ) : (
          <div className="relative rounded-lg">
            <div
              className="overflow-hidden outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              ref={emblaRef}
              role="region"
              aria-label="Property photos"
              tabIndex={canLoop ? 0 : undefined}
              onKeyDown={onViewportKeyDown}
            >
              <div className="flex gap-2">
                {gallery.map((src, i) => (
                  <div key={`${i}-${src}`} className={TILE}>
                    <Image
                      src={src}
                      alt={`${imageTitle} — photo ${i + 1} of ${gallery.length}`}
                      fill
                      className="object-cover"
                      sizes="(max-width: 640px) 50vw, 50vw"
                      priority={i === 0}
                    />
                  </div>
                ))}
              </div>
            </div>

            {canLoop ? (
              <>
                <Button
                  type="button"
                  size="icon"
                  variant="secondary"
                  className="absolute left-2 top-1/2 z-[2] size-10 -translate-y-1/2 rounded-full border border-border bg-background/95 shadow-md sm:left-3"
                  aria-label="Previous photos"
                  onClick={scrollPrev}
                >
                  <ChevronLeft className="size-5" />
                </Button>
                <Button
                  type="button"
                  size="icon"
                  variant="secondary"
                  className="absolute right-2 top-1/2 z-[2] size-10 -translate-y-1/2 rounded-full border border-border bg-background/95 shadow-md sm:right-3"
                  aria-label="Next photos"
                  onClick={scrollNext}
                >
                  <ChevronRight className="size-5" />
                </Button>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};
