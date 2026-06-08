"use client";

import { Button, type ButtonProps } from "@components/ui/voyager/button";
import { cn } from "@utils/common";

/**
 * Voyager-styled primary button (pill shape, indigo).
 *
 * Ported from Voyager's `shared/ButtonPrimary.tsx` as a thin wrapper over the
 * base `Button`. Voyager's `bg-primary-6000` typo is corrected to
 * `bg-primary-600`. Uses the `primary-*` tokens added in globals.css.
 */
export type ButtonPrimaryProps = ButtonProps;

export const ButtonPrimary = ({ className, ...props }: ButtonPrimaryProps) => (
  <Button
    className={cn(
      "bg-primary-600 text-neutral-50 hover:bg-primary-700 disabled:opacity-70",
      className,
    )}
    {...props}
  />
);

