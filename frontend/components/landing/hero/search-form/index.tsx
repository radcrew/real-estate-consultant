"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { cn } from "@utils/common";
import { searchService } from "@services/search";

import { LocationInput } from "./location-input";
import { PriceRangeInput } from "./price-range-input";
import {
  DEFAULT_PROPERTY_TYPES,
  PropertyTypeSelect,
  type PropertyTypeOption,
} from "./property-type-select";

type HeroRealEstateSearchFormProps = {
  className?: string;
};

export const HeroRealEstateSearchForm = ({ className }: HeroRealEstateSearchFormProps) => {
  const router = useRouter();
  const [location, setLocation] = useState("");
  const [propertyTypes, setPropertyTypes] = useState<PropertyTypeOption[]>(DEFAULT_PROPERTY_TYPES);
  const [priceRange, setPriceRange] = useState<[number, number]>([100000, 4000000]);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const selectedTypes = propertyTypes
        .filter((t) => t.checked)
        .map((t) => t.name);
      const { search_profile_id } = await searchService.quickSearch({
        location: location.trim() || undefined,
        property_types: selectedTypes.length ? selectedTypes : undefined,
        price_min: priceRange[0],
        price_max: priceRange[1],
      });
      router.push(`/search/${search_profile_id}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={cn("mx-auto w-full max-w-6xl py-5 lg:py-0", className)}>
      <form
        className="relative flex w-full flex-col divide-y divide-neutral-200 rounded-3xl bg-white shadow-xl dark:divide-neutral-700 dark:bg-neutral-800 dark:shadow-2xl lg:flex-row lg:items-center lg:divide-y-0 lg:rounded-full"
        onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
      >
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
          onSubmit={handleSubmit}
          submitting={submitting}
        />
      </form>
    </div>
  );
};
