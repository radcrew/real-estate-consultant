import type { ReactNode } from "react";

import { ButtonSecondary } from "@components/ui/button-secondary";
import { Heading2 } from "@components/ui/heading2";
import type { PropertyModel } from "@typings/property";
import { PropertyCard, PROPERTY_GRID } from "@components/property/property-card";
import { cn } from "@utils/common";

/**
 * Voyager-style featured grid section: heading + a responsive `PropertyCard`
 * grid + an optional browse CTA. Ported from Voyager's
 * `SectionGridFeatureProperty`, but data-driven by `PropertyModel[]`. Reused by
 * the home featured grid and the listings page.
 */
export interface SectionGridFeaturePropertyProps {
  heading?: ReactNode;
  subHeading?: ReactNode;
  data: PropertyModel[];
  cta?: { label: string; href: string };
  gridClassName?: string;
  className?: string;
}

export const SectionGridFeatureProperty = ({
  heading,
  subHeading,
  data,
  cta,
  gridClassName = PROPERTY_GRID,
  className,
}: SectionGridFeaturePropertyProps) => (
  <section className={cn("relative", className)}>
    {(heading || subHeading) && (
      <Heading2 heading={heading} subHeading={subHeading} />
    )}

    <div className={gridClassName}>
      {data.map((item) => (
        <PropertyCard key={item.id} data={item} />
      ))}
    </div>

    {cta && (
      <div className="mt-14 flex justify-center">
        <ButtonSecondary href={cta.href}>{cta.label}</ButtonSecondary>
      </div>
    )}
  </section>
);
