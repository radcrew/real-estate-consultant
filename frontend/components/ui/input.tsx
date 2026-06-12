"use client";

import type { InputHTMLAttributes, Ref } from "react";

import { cn } from "@utils/common";

/**
 * App text input (Voyager-styled).
 *
 * Ported from Voyager's `shared/Input.tsx`. Adapted to this stack: `cn()`,
 * React 19 `ref`-as-prop (no `forwardRef`), and Tailwind v4 focus syntax.
 * Looks best with the @tailwindcss/forms plugin.
 */
export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  sizeClass?: string;
  fontClass?: string;
  rounded?: string;
  ref?: Ref<HTMLInputElement>;
}

export const Input = ({
  className,
  sizeClass = "h-11 px-4 py-3",
  fontClass = "text-sm font-normal",
  rounded = "rounded-2xl",
  type = "text",
  ref,
  ...props
}: InputProps) => (
  <input
    ref={ref}
    type={type}
    className={cn(
      "block w-full border-neutral-200 bg-white",
      "focus:border-primary-300 focus:ring-2 focus:ring-primary-200/50",
      "dark:border-neutral-700 dark:bg-neutral-900 dark:focus:ring-primary-600/25",
      rounded,
      fontClass,
      sizeClass,
      className,
    )}
    {...props}
  />
);
