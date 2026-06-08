import type { ReactNode } from "react";

import { ButtonSecondary } from "@components/ui/voyager/button-secondary";
import { Heading2 } from "@components/ui/voyager/heading2";
import type { PropertyModel } from "@components/voyager/listing-model";
import { PropertyCard } from "@components/voyager/property-card";
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
  gridClassName = "grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-8 lg:grid-cols-3",
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
