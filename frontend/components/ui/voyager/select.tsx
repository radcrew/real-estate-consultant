"use client";

import type { Ref, SelectHTMLAttributes } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled select.
 *
 * Ported from Voyager's `shared/Select.tsx`. Adapted to this stack: `cn()`,
 * React 19 `ref`-as-prop, and Tailwind v4 focus syntax.
 */
export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  sizeClass?: string;
  ref?: Ref<HTMLSelectElement>;
}

export const Select = ({
  className,
  sizeClass = "h-11",
  ref,
  children,
  ...props
}: SelectProps) => (
  <select
    ref={ref}
    className={cn(
      "block w-full rounded-2xl border-neutral-200 bg-white text-sm",
      "focus:border-primary-300 focus:ring-2 focus:ring-primary-200/50",
      "dark:border-neutral-700 dark:bg-neutral-900 dark:focus:ring-primary-600/25",
      sizeClass,
      className,
    )}
    {...props}
  >
    {children}
  </select>
);

