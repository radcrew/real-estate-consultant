import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Centered, bordered card used for empty / not-found / error states across the
 * saved, agent, search-results and admin views.
 */
export const NoticeCard = ({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) => (
  <div
    className={cn(
      "rounded-2xl border border-neutral-200 p-10 text-center dark:border-neutral-700",
      className,
    )}
  >
    {children}
  </div>
);
