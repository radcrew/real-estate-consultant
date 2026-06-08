"use client";

import { useState, type ReactNode } from "react";

import { Heading2 } from "@components/ui/heading2";
import type { PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
import { PropertyMap } from "@components/voyager/property-map";

/**
 * Voyager-style grid + map split, ported from Voyager's `SectionGridHasMap`:
 * a `PropertyCard` list and a `PropertyMap` with the active marker synced to card
 * hover (and card highlight synced to marker click). Responsive: on smaller
 * screens the map sits on top at a fixed height (so it's always visible when this
 * view is chosen); on xl it becomes a sticky side panel. Data-driven by
 * `PropertyModel[]`. Sticky offset assumes the h-20 header.
 */
export interface SectionGridHasMapProps {
  data: PropertyModel[];
  heading?: ReactNode;
  subHeading?: ReactNode;
}

export const SectionGridHasMap = ({
  data,
  heading,
  subHeading,
}: SectionGridHasMapProps) => {
  const [activeId, setActiveId] = useState<string | undefined>(undefined);

  return (
    <div className="flex flex-col-reverse gap-8 xl:flex-row xl:gap-0">
      <div className="w-full xl:w-3/5 xl:px-8 2xl:w-1/2">
        {(heading || subHeading) && (
          <Heading2 heading={heading} subHeading={subHeading} />
        )}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          {data.map((item) => (
            <div
              key={item.id}
              onMouseEnter={() => setActiveId(item.id)}
              onMouseLeave={() => setActiveId(undefined)}
            >
              <PropertyCard data={item} />
            </div>
          ))}
        </div>
      </div>

      <div className="w-full xl:flex-1">
        <div className="h-[360px] sm:h-[460px] xl:sticky xl:top-20 xl:h-[calc(100vh-5rem)] xl:py-6">
          <PropertyMap
            items={data}
            activeId={activeId}
            onMarkerClick={setActiveId}
            className="h-full"
          />
        </div>
      </div>
    </div>
  );
};
