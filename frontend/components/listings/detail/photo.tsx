"use client";

import Image from "next/image";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@components/ui/button";
import { cn } from "@utils/common";

import { useImagesPerSlide } from "./hooks/use-images-per-slide";
import { useListingPhotoCarousel } from "./hooks/use-listing-photo-carousel";

type ListingPhotoCarouselProps = {
  gallery: string[];
  imageTitle: string;
};

export const ListingPhotoCarousel = ({ gallery, imageTitle }: ListingPhotoCarouselProps) => {
  const perSlide = useImagesPerSlide();
  const {
    slides,
    slideCount,
    safeSlide,
    carouselTransition,
    goPrevious,
    goNext,
  } = useListingPhotoCarousel(gallery, perSlide);

  return (
    <div className="w-full overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      <div className="relative bg-muted/40 p-3 sm:p-4">
        {gallery.length === 0 ? (
          <div className="flex min-h-[200px] items-center justify-center text-sm text-muted-foreground">
            No photos
          </div>
        ) : (
          <>
            <div
              className="overflow-hidden rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              role="region"
              aria-roledescription="carousel"
              aria-label="Property photos"
              tabIndex={slideCount > 1 ? 0 : undefined}
            >
              <div
                className={cn(
                  "flex",
                  carouselTransition && "transition-transform duration-300 ease-out",
                )}
                style={{ transform: `translateX(-${safeSlide * 100}%)` }}
              >
                {slides.map((slice, slideIndex) => (
                  <div
                    key={slideIndex}
                    className="min-w-full shrink-0 px-0.5"
                    aria-hidden={slideIndex !== safeSlide}
                  >
                    <div
                      className={cn(
                        "grid gap-3 sm:gap-4",
                        perSlide === 1 && "grid-cols-1",
                        perSlide === 2 && "grid-cols-2",
                        perSlide === 3 && "grid-cols-3",
                      )}
                    >
                      {slice.map((src, i) => {
                        const photoIndex = (slideIndex + i) % gallery.length;
                        return (
                          <div
                            key={`${slideIndex}-${i}-${photoIndex}`}
                            className="relative aspect-[4/3] w-full overflow-hidden rounded-md bg-muted"
                          >
                            <Image
                              src={src}
                              alt={`${imageTitle} — photo ${photoIndex + 1} of ${gallery.length}`}
                              fill
                              className="object-cover"
                              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                              priority={slideIndex === 0 && i === 0}
                            />
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {slideCount > 1 ? (
              <div className="mt-4 flex items-center justify-between gap-3">
                <Button
                  type="button"
                  size="icon"
                  variant="secondary"
                  className="size-10 shrink-0 rounded-full border border-border bg-background shadow-sm"
                  aria-label="Previous photos"
                  onClick={goPrevious}
                >
                  <ChevronLeft className="size-5" />
                </Button>
                <span className="text-xs font-medium tabular-nums text-muted-foreground">
                  {safeSlide + 1} / {slideCount}
                </span>
                <Button
                  type="button"
                  size="icon"
                  variant="secondary"
                  className="size-10 shrink-0 rounded-full border border-border bg-background shadow-sm"
                  aria-label="Next photos"
                  onClick={goNext}
                >
                  <ChevronRight className="size-5" />
                </Button>
              </div>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
};
