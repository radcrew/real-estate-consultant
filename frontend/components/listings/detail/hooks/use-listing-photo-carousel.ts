"use client";

import type { KeyboardEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { circularWindow } from "@utils/listings";

export function useListingPhotoCarousel(gallery: string[], perSlide: number) {
  const slideCount = gallery.length;
  const slides = useMemo(() => {
    if (gallery.length === 0) {
      return [] as string[][];
    }
    return gallery.map((_, startIdx) => circularWindow(gallery, startIdx, perSlide));
  }, [gallery, perSlide]);

  const [slide, setSlide] = useState(0);
  const [carouselTransition, setCarouselTransition] = useState(true);

  const safeSlide = slideCount === 0 ? 0 : Math.min(slide, slideCount - 1);

  const goSlide = useCallback(
    (delta: number) => {
      if (slideCount <= 1) {
        return;
      }
      setSlide((s) => {
        const maxIdx = Math.max(0, slideCount - 1);
        const s0 = Math.min(Math.max(s, 0), maxIdx);
        const raw = s0 + delta;
        const next = ((raw % slideCount) + slideCount) % slideCount;
        const wrapped = raw < 0 || raw >= slideCount;
        if (wrapped) {
          queueMicrotask(() => {
            setCarouselTransition(false);
          });
        }
        return next;
      });
    },
    [slideCount],
  );

  useEffect(() => {
    if (!carouselTransition) {
      const id = requestAnimationFrame(() => {
        setCarouselTransition(true);
      });
      return () => cancelAnimationFrame(id);
    }
  }, [carouselTransition]);

  const goPrevious = useCallback(() => goSlide(-1), [goSlide]);
  const goNext = useCallback(() => goSlide(1), [goSlide]);

  return {
    slides,
    slideCount,
    safeSlide,
    carouselTransition,
    goPrevious,
    goNext,
  };
}
