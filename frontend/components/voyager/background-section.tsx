import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager `BackgroundSection`: a full-bleed, rounded tinted panel positioned
 * absolutely behind a section's content. Ported verbatim from Voyager's
 * `components/BackgroundSection.tsx` (Tailwind classes carry over unchanged).
 */
type BackgroundSectionProps = {
  className?: string;
  children?: ReactNode;
};

export const BackgroundSection = ({
  className = "bg-neutral-100 dark:bg-black/20",
  children,
}: BackgroundSectionProps) => (
  <div
    className={cn(
      "absolute inset-y-0 left-1/2 z-0 w-screen -translate-x-1/2 xl:max-w-[1340px] xl:rounded-[40px] 2xl:max-w-screen-2xl",
      className,
    )}
  >
    {children}
  </div>
);
