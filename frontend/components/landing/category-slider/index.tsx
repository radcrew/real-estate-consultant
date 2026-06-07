"use client";

import useEmblaCarousel from "embla-carousel-react";

import { NextPrev } from "@components/ui/voyager/next-prev";
import { cn } from "@utils/common";

import { CardCategory, type CardType } from "./card-category";
import type { Category } from "./data";

/**
 * Category slider, ported from Voyager's `SectionSliderNewCategories`. Voyager's
 * framer-motion + react-swipeable + react-use stack is replaced with the
 * already-installed `embla-carousel-react`; controls use the `NextPrev` atom.
 */
type CategorySliderProps = {
  heading: string;
  subHeading: string;
  categories: Category[];
  cardType: CardType;
  /** Per-slide responsive width (mirrors Voyager's itemPerRow). */
  slideClassName: string;
};

export const CategorySlider = ({
  heading,
  subHeading,
  categories,
  cardType,
  slideClassName,
}: CategorySliderProps) => {
  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: "start",
    containScroll: "trimSnaps",
  });

  return (
    <div className="relative">
      <div className="flex flex-col justify-between sm:flex-row sm:items-end">
        <div className="max-w-2xl">
          <h2 className="text-3xl font-semibold md:text-4xl">{heading}</h2>
          <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
            {subHeading}
          </span>
        </div>
        <NextPrev
          className="mt-4 hidden sm:mt-0 sm:flex"
          onClickPrev={() => emblaApi?.scrollPrev()}
          onClickNext={() => emblaApi?.scrollNext()}
        />
      </div>

      <div className="mt-10 overflow-hidden" ref={emblaRef}>
        <div className="-ml-3 flex xl:-ml-5">
          {categories.map((category) => (
            <div
              key={category.id}
              className={cn("min-w-0 shrink-0 grow-0 pl-3 xl:pl-5", slideClassName)}
            >
              <CardCategory category={category} cardType={cardType} />
            </div>
          ))}
        </div>
      </div>

      <NextPrev
        className="mt-6 flex justify-center sm:hidden"
        onClickPrev={() => emblaApi?.scrollPrev()}
        onClickNext={() => emblaApi?.scrollNext()}
      />
    </div>
  );
};
