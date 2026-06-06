import type { ReactNode } from "react";

import { cn } from "@utils/common";

type ListingDetailNoticeProps = {
  title?: string;
  message: string;
  tone?: "neutral" | "error";
  action?: ReactNode;
};

export const ListingDetailNotice = ({
  title,
  message,
  tone = "neutral",
  action,
}: ListingDetailNoticeProps) => (
  <div
    className={cn(
      "rounded-2xl border p-8 text-center",
      tone === "error"
        ? "border-red-200 bg-red-50 dark:border-red-900/40 dark:bg-red-950/20"
        : "border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900",
    )}
  >
    {title && (
      <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
        {title}
      </h2>
    )}
    <p
      className={cn(
        "text-sm",
        title && "mt-2",
        tone === "error"
          ? "text-red-600 dark:text-red-400"
          : "text-neutral-500 dark:text-neutral-400",
      )}
    >
      {message}
    </p>
    {action && <div className="mt-5 flex justify-center">{action}</div>}
  </div>
);

export const ListingDetailSkeleton = () => (
  <div className="space-y-10">
    <div className="grid h-80 grid-cols-2 grid-rows-2 gap-1 overflow-hidden rounded-2xl sm:h-[460px] sm:grid-cols-4 sm:gap-2">
      <div className="col-span-2 row-span-2 animate-pulse bg-neutral-100 dark:bg-neutral-800" />
      {Array.from({ length: 4 }, (_, i) => (
        <div
          key={i}
          className="hidden animate-pulse bg-neutral-100 sm:block dark:bg-neutral-800"
        />
      ))}
    </div>
    <div className="lg:grid lg:grid-cols-[1fr_22rem] lg:gap-10">
      <div className="space-y-3">
        <div className="h-7 w-3/4 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
        <div className="h-24 w-full animate-pulse rounded bg-neutral-100 dark:bg-neutral-800" />
      </div>
      <div className="mt-8 h-56 animate-pulse rounded-2xl bg-neutral-100 lg:mt-0 dark:bg-neutral-800" />
    </div>
  </div>
);
