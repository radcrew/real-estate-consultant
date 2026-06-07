import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Section heading ported from Voyager's `shared/Heading.tsx` — `text-3xl
 * md:text-4xl font-semibold` title with a `text-base sm:text-lg` neutral-500
 * description. Supports Voyager's centered variant and an optional right-aligned
 * actions slot (e.g. slider controls).
 */
type SectionHeadingProps = {
  children: ReactNode;
  desc?: ReactNode;
  isCenter?: boolean;
  actions?: ReactNode;
  className?: string;
};

export const SectionHeading = ({
  children,
  desc,
  isCenter = false,
  actions,
  className = "mb-10 text-neutral-900 dark:text-neutral-50",
}: SectionHeadingProps) => (
  <div
    className={cn(
      "relative",
      actions && "flex flex-col justify-between sm:flex-row sm:items-end",
      className,
    )}
  >
    <div className={isCenter ? "mx-auto mb-4 w-full max-w-2xl text-center" : "max-w-2xl"}>
      <h2 className="text-3xl font-semibold md:text-4xl">{children}</h2>
      {desc && (
        <span className="mt-2 block text-base font-normal text-neutral-500 dark:text-neutral-400 sm:text-lg md:mt-3">
          {desc}
        </span>
      )}
    </div>
    {actions && <div className="mt-4 flex-shrink-0 sm:mt-0">{actions}</div>}
  </div>
);
