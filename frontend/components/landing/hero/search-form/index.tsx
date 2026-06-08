"use client";

import { useState } from "react";

import { cn } from "@utils/common";

import { LocationInput } from "./location-input";
import { PriceRangeInput } from "./price-range-input";
import {
  DEFAULT_PROPERTY_TYPES,
  PropertyTypeSelect,
  type PropertyTypeOption,
} from "./property-type-select";

export type RealEstateTab = "Buy" | "Rent" | "Sell";

const TABS: RealEstateTab[] = ["Buy", "Rent", "Sell"];

/** Where the hero search routes — the app's real intake/search entry point. */
const SUBMIT_HREF = "/questionnaire";

type HeroRealEstateSearchFormProps = {
  className?: string;
  currentTab?: RealEstateTab;
};

export const HeroRealEstateSearchForm = ({
  className,
  currentTab = "Buy",
}: HeroRealEstateSearchFormProps) => {
  const [tabActive, setTabActive] = useState<RealEstateTab>(currentTab);
  const [location, setLocation] = useState("");
  const [propertyTypes, setPropertyTypes] =
    useState<PropertyTypeOption[]>(DEFAULT_PROPERTY_TYPES);
  const [priceRange, setPriceRange] = useState<[number, number]>([100000, 4000000]);

  return (
    <div className={cn("mx-auto w-full max-w-6xl py-5 lg:py-0", className)}>
      <ul className="ml-5 inline-flex space-x-5 rounded-t-3xl bg-white px-4 pt-2 pb-6 dark:bg-neutral-800 md:ml-10 md:space-x-8 md:px-7 md:pt-3 lg:space-x-11 xl:px-8">
        {TABS.map((tab) => {
          const active = tab === tabActive;
          return (
            <li
              key={tab}
              onClick={() => setTabActive(tab)}
              className={cn(
                "flex cursor-pointer items-center text-sm font-medium leading-none lg:text-base",
                !active &&
                  "text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-100",
              )}
            >
              <span
                className={cn(
                  "mr-2 block size-2.5 rounded-full bg-neutral-800 dark:bg-neutral-100",
                  !active && "invisible",
                )}
              />
              <span>{tab}</span>
            </li>
          );
        })}
      </ul>

      <form className="relative flex w-full flex-col divide-y divide-neutral-200 rounded-3xl bg-white shadow-xl dark:divide-neutral-700 dark:bg-neutral-800 dark:shadow-2xl lg:flex-row lg:items-center lg:divide-y-0 lg:rounded-full">
        <LocationInput
          className="flex-[1.5]"
          value={location}
          onChange={setLocation}
        />

        <div className="h-8 self-center border-r border-slate-200 dark:border-slate-700" />
        <PropertyTypeSelect value={propertyTypes} onChange={setPropertyTypes} />

        <div className="h-8 self-center border-r border-slate-200 dark:border-slate-700" />
        <PriceRangeInput
          value={priceRange}
          onChange={setPriceRange}
          submitHref={SUBMIT_HREF}
        />
      </form>
    </div>
  );
};
