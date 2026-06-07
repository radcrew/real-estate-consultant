import Image from "next/image";

import { cn } from "@utils/common";

import { HeroRealEstateSearchForm } from "./search-form";

/**
 * Voyager `SectionHero2` ported into this app: full-bleed hero image on the
 * right, an angled `primary-500` panel with the headline, and the real-estate
 * search bar below. Markup mirrors Voyager; icons/atoms adapted to this stack.
 */
type SectionHero2Props = {
  className?: string;
};

export const SectionHero2 = ({ className }: SectionHero2Props) => (
  <div className={cn("relative", className)}>
    <div className="absolute inset-y-0 right-0 w-5/6 flex-grow xl:w-3/4">
      <Image
        fill
        priority
        className="object-cover"
        src="/images/hero-right-3.png"
        alt="Modern commercial property"
        sizes="(max-width: 1280px) 83vw, 75vw"
      />
    </div>
    <div className="relative py-14 lg:py-20">
      <div className="relative inline-flex">
        <div className="absolute inset-y-0 right-20 w-screen bg-primary-500 md:right-52" />
        <div className="relative inline-flex max-w-3xl flex-shrink-0 flex-col items-start space-y-8 py-16 text-white sm:space-y-10 sm:py-20 lg:py-24">
          <h2 className="text-4xl font-semibold !leading-[110%] md:text-5xl xl:text-7xl">
            Find Your Best <br /> Smart Real Estate
          </h2>
        </div>
      </div>
      <div className="hidden w-full lg:mt-20 lg:block">
        <HeroRealEstateSearchForm />
      </div>
    </div>
  </div>
);
