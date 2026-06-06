import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled section heading with optional sub-heading.
 * Ported from Voyager's `shared/Heading2.tsx`; travel-specific demo defaults
 * removed (heading/sub-heading now render only when provided).
 */
export interface Heading2Props {
  heading?: ReactNode;
  subHeading?: ReactNode;
  className?: string;
}

export const Heading2 = ({ className, heading, subHeading }: Heading2Props) => (
  <div className={cn("mb-12 lg:mb-16", className)}>
    {heading && <h2 className="text-4xl font-semibold">{heading}</h2>}
    {subHeading}
  </div>
);

export default Heading2;
