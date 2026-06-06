"use client";

import { useState, type ReactNode } from "react";

import { Heading2 } from "@components/ui/voyager/heading2";
import type { PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
import { PropertyMap } from "@components/voyager/property-map";

/**
 * Voyager-style grid + map split, ported from Voyager's `SectionGridHasMap`:
 * a scrollable `PropertyCard` list on the left and a sticky `PropertyMap` on the
 * right, with the active marker synced to card hover (and card highlight synced
 * to marker click). Data-driven by `PropertyModel[]`. The map column is hidden
 * below xl. Sticky offset assumes the h-20 header.
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
    <div className="relative flex">
      <div className="min-h-screen w-full shrink-0 xl:w-3/5 xl:px-8 2xl:w-1/2">
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

      <div className="hidden xl:block xl:flex-1">
        <div className="sticky top-20 h-[calc(100vh-5rem)] py-6">
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

export default SectionGridHasMap;
