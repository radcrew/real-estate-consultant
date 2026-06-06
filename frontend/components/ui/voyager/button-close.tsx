"use client";

import { X } from "lucide-react";

import { cn } from "@utils/common";

/**
 * Voyager-styled close button (X icon).
 *
 * Ported from Voyager's `shared/ButtonClose.tsx`. The Heroicons `XMarkIcon` is
 * swapped for lucide's `X` (this repo's icon set), and Voyager's
 * `twFocusClass()` helper is inlined as `focus:outline-none`.
 */
export interface ButtonCloseProps {
  className?: string;
  onClick?: () => void;
}

export const ButtonClose = ({ className, onClick }: ButtonCloseProps) => (
  <button
    type="button"
    className={cn(
      "flex h-8 w-8 items-center justify-center rounded-full text-neutral-700 hover:bg-neutral-100",
      "focus:outline-none dark:text-neutral-300 dark:hover:bg-neutral-700",
      className,
    )}
    onClick={onClick}
  >
    <span className="sr-only">Close</span>
    <X className="h-5 w-5" />
  </button>
);

export default ButtonClose;
