import Image from "next/image";

import { ButtonPrimary } from "@components/ui/button-primary";
import { brand } from "@config/brand";
import { cn } from "@utils/common";

import { HeroRealEstateSearchForm } from "./search-form";

/**
 * Voyager `SectionHero` (stay-home style) ported into this app: heading +
 * subtitle + CTA on the left, large image on the right, and the search form
 * floating below with an upward overlap. Copy comes from `config/brand`.
 */
type SectionHeroProps = {
  className?: string;
};

export const SectionHero = ({ className }: SectionHeroProps) => (
  <div className={cn("relative flex flex-col-reverse lg:flex-col", className)}>
    <div className="flex flex-col lg:flex-row lg:items-center">
      <div className="flex flex-shrink-0 flex-col items-start space-y-8 pb-14 sm:space-y-10 lg:mr-10 lg:w-1/2 lg:pb-64 xl:mr-0 xl:pr-14">
        <h2 className="text-4xl font-medium !leading-[114%] md:text-5xl xl:text-7xl">
          {brand.hero.title}
        </h2>
        <span className="text-base text-neutral-500 md:text-lg dark:text-neutral-400">
          {brand.hero.subtitle}
        </span>
        <ButtonPrimary href={brand.hero.primaryCta.href} sizeClass="px-5 py-4 sm:px-7">
          {brand.hero.primaryCta.label}
        </ButtonPrimary>
      </div>
      <div className="flex-grow">
        <Image
          className="h-auto w-full"
          src="/images/hero-right.png"
          width={1001}
          height={1031}
          alt="Commercial real estate"
          priority
        />
      </div>
    </div>

    <div className="z-10 mb-12 hidden w-full lg:-mt-40 lg:mb-0 lg:block">
      <HeroRealEstateSearchForm />
    </div>
  </div>
);
