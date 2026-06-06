import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled section heading with optional description.
 * Ported from Voyager's `shared/Heading.tsx`; the demo `desc` default is dropped
 * (renders only when provided) and `fontClass` is now actually applied to the h2.
 */
export interface HeadingProps extends HTMLAttributes<HTMLHeadingElement> {
  fontClass?: string;
  desc?: ReactNode;
  isCenter?: boolean;
}

export const Heading = ({
  children,
  desc,
  className = "mb-10 text-neutral-900 dark:text-neutral-50",
  fontClass = "text-3xl md:text-4xl font-semibold",
  isCenter = false,
  ...props
}: HeadingProps) => (
  <div className={cn("relative", className)}>
    <div className={isCenter ? "mx-auto mb-4 w-full max-w-2xl text-center" : "max-w-2xl"}>
      <h2 className={fontClass} {...props}>
        {children}
      </h2>
      {desc && (
        <span className="mt-2 block text-base font-normal text-neutral-500 sm:text-lg md:mt-3 dark:text-neutral-400">
          {desc}
        </span>
      )}
    </div>
  </div>
);

export default Heading;
