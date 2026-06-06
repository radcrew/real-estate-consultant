"use client";

import Link from "next/link";

import { cn } from "@utils/common";

/**
 * Voyager-styled tag chip (links to a taxonomy/category).
 *
 * Ported from Voyager's `shared/Tag.tsx`. Decoupled from Voyager's
 * `TaxonomyType`: takes plain `name`/`href`/`count` props instead. Voyager's
 * `neutral-6000` typo is corrected to `neutral-600`.
 */
export interface TagProps {
  className?: string;
  name: string;
  href: string;
  count?: number;
  hideCount?: boolean;
}

export const Tag = ({
  className,
  name,
  href,
  count,
  hideCount = false,
}: TagProps) => (
  <Link
    href={href}
    className={cn(
      "inline-block rounded-lg border border-neutral-100 bg-white px-3 py-2 text-sm text-neutral-600",
      "hover:border-neutral-200 md:px-4 md:py-2.5",
      "dark:border-neutral-700 dark:bg-neutral-700 dark:text-neutral-300 dark:hover:border-neutral-600",
      className,
    )}
  >
    {name}
    {!hideCount && count !== undefined && (
      <span className="text-xs font-normal"> ({count})</span>
    )}
  </Link>
);

export default Tag;
