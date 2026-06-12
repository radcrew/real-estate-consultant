"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { cn } from "@utils/common";

/**
 * Voyager-styled prev/next circular controls (e.g. carousels).
 *
 * Ported from Voyager's `shared/NextPrev.tsx`. line-awesome chevrons swapped for
 * lucide, `twFocusClass()` inlined as `focus:outline-none`, and the
 * `neutral-6000` typo corrected to `neutral-600`. Unused `currentPage`/
 * `totalPage` props dropped.
 */
export interface NextPrevProps {
  className?: string;
  btnClassName?: string;
  onClickNext?: () => void;
  onClickPrev?: () => void;
  onlyNext?: boolean;
  onlyPrev?: boolean;
}

export const NextPrev = ({
  className,
  btnClassName = "w-10 h-10",
  onClickNext,
  onClickPrev,
  onlyNext = false,
  onlyPrev = false,
}: NextPrevProps) => {
  const btnBase = cn(
    "flex items-center justify-center rounded-full border border-neutral-200 bg-white",
    "hover:border-neutral-300 focus:outline-none",
    "dark:border-neutral-600 dark:bg-neutral-900 dark:hover:border-neutral-500",
  );

  return (
    <div
      className={cn(
        "relative flex items-center text-neutral-900 dark:text-neutral-300",
        className,
      )}
    >
      {!onlyNext && (
        <button
          type="button"
          className={cn(btnClassName, !onlyPrev && "mr-1.5", btnBase)}
          onClick={onClickPrev}
          title="Prev"
        >
          <ChevronLeft className="h-5 w-5" />
        </button>
      )}
      {!onlyPrev && (
        <button
          type="button"
          className={cn(btnClassName, btnBase)}
          onClick={onClickNext}
          title="Next"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      )}
    </div>
  );
};

