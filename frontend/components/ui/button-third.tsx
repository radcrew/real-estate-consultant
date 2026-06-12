"use client";

import { Button, type ButtonProps } from "@components/ui/button";
import { cn } from "@utils/common";

/**
 * Voyager-styled "third" button (transparent surface, neutral border/text).
 * Ported from Voyager's `shared/ButtonThird.tsx` as a wrapper over `Button`.
 */
export type ButtonThirdProps = ButtonProps;

export const ButtonThird = ({ className, ...props }: ButtonThirdProps) => (
  <Button
    className={cn(
      "border border-neutral-200 text-neutral-700",
      "dark:border-neutral-700 dark:text-neutral-200",
      className,
    )}
    {...props}
  />
);

