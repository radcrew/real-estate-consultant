"use client";

import type { Ref, TextareaHTMLAttributes } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled textarea.
 *
 * Ported from Voyager's `shared/Textarea.tsx`. Adapted to this stack: `cn()`,
 * React 19 `ref`-as-prop, and Tailwind v4 focus syntax. `rows` is now an
 * overridable prop (default 4) instead of being hard-coded.
 */
export interface TextareaProps
  extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  ref?: Ref<HTMLTextAreaElement>;
}

export const Textarea = ({
  className,
  rows = 4,
  ref,
  children,
  ...props
}: TextareaProps) => (
  <textarea
    ref={ref}
    rows={rows}
    className={cn(
      "block w-full rounded-2xl border-neutral-200 bg-white text-sm",
      "focus:border-primary-300 focus:ring-2 focus:ring-primary-200/50",
      "dark:border-neutral-700 dark:bg-neutral-900 dark:focus:ring-primary-600/25",
      className,
    )}
    {...props}
  >
    {children}
  </textarea>
);

export default Textarea;
