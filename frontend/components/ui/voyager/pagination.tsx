"use client";

import Link from "next/link";

import { cn } from "@utils/common";

/**
 * Voyager-styled pagination.
 *
 * Ported from Voyager's `shared/Pagination.tsx`. Decoupled from the demo data /
 * `CustomLink` type — it now takes real `items` and an `activeIndex`. Typos
 * fixed (`primary-6000` -> `primary-600`, `neutral-6000` -> `neutral-600`) and
 * `twFocusClass()` inlined as `focus:outline-none`.
 */
export interface PaginationItem {
  label: string;
  href?: string;
}

export interface PaginationProps {
  className?: string;
  items?: PaginationItem[];
  activeIndex?: number;
  /** When set, items render as buttons calling this (client-side paging). */
  onPageClick?: (index: number) => void;
}

const INACTIVE_CLASS = cn(
  "inline-flex h-11 w-11 items-center justify-center rounded-full border border-neutral-200 bg-white text-neutral-600 hover:bg-neutral-100 focus:outline-none",
  "dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800",
);

export const Pagination = ({
  className,
  items = [],
  activeIndex = 0,
  onPageClick,
}: PaginationProps) => (
  <nav className={cn("inline-flex space-x-1 text-base font-medium", className)}>
    {items.map((item, index) => {
      const key = `${item.href ?? "page"}-${index}`;
      if (index === activeIndex) {
        return (
          <span
            key={key}
            aria-current="page"
            className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-primary-600 text-white focus:outline-none"
          >
            {item.label}
          </span>
        );
      }
      if (onPageClick) {
        return (
          <button
            key={key}
            type="button"
            onClick={() => onPageClick(index)}
            className={INACTIVE_CLASS}
          >
            {item.label}
          </button>
        );
      }
      return (
        <Link key={key} href={item.href ?? "#"} className={INACTIVE_CLASS}>
          {item.label}
        </Link>
      );
    })}
  </nav>
);

export default Pagination;
