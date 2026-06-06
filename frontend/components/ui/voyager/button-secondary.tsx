"use client";

import { Button, type ButtonProps } from "@components/ui/voyager/button";
import { cn } from "@utils/common";

/**
 * Voyager-styled secondary button (white surface, neutral border).
 * Ported from Voyager's `shared/ButtonSecondary.tsx` as a wrapper over `Button`.
 */
export interface ButtonSecondaryProps extends ButtonProps {}

export const ButtonSecondary = ({
  className,
  ...props
}: ButtonSecondaryProps) => (
  <Button
    className={cn(
      "border border-neutral-200 bg-white font-medium text-neutral-700 hover:bg-neutral-100",
      "dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-300 dark:hover:bg-neutral-800",
      className,
    )}
    {...props}
  />
);

export default ButtonSecondary;
