"use client";

import type { ButtonHTMLAttributes } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled circular icon button (indigo).
 *
 * Ported from Voyager's `shared/ButtonCircle.tsx`. Unlike the text buttons this
 * is a raw `<button>` (not built on the base `Button`). Voyager's
 * `bg-primary-6000` typo is corrected to `bg-primary-600`.
 */
export interface ButtonCircleProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: string;
}

export const ButtonCircle = ({
  className,
  size = "w-9 h-9",
  ...props
}: ButtonCircleProps) => (
  <button
    className={cn(
      "flex items-center justify-center rounded-full leading-none! text-neutral-50",
      "bg-primary-600 hover:bg-primary-700 disabled:opacity-70",
      size,
      className,
    )}
    {...props}
  />
);

