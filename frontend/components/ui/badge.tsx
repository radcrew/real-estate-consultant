"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled badge (pill, colored).
 *
 * Ported from Voyager's `shared/Badge.tsx`. Decoupled from Voyager's data layer:
 * the `TwMainColor`/`Route` imports are replaced with a local `BadgeColor` type
 * and `string` hrefs. Color classes are kept as static strings (Tailwind can't
 * see dynamically-built class names).
 */
export type BadgeColor =
  | "pink"
  | "red"
  | "gray"
  | "green"
  | "purple"
  | "indigo"
  | "yellow"
  | "blue";

const COLOR_BASE: Record<BadgeColor, string> = {
  pink: "text-pink-800 bg-pink-100",
  red: "text-red-800 bg-red-100",
  gray: "text-gray-800 bg-gray-100",
  green: "text-green-800 bg-green-100",
  purple: "text-purple-800 bg-purple-100",
  indigo: "text-indigo-800 bg-indigo-100",
  yellow: "text-yellow-800 bg-yellow-100",
  blue: "text-blue-800 bg-blue-100",
};

const COLOR_HOVER: Record<BadgeColor, string> = {
  pink: "hover:bg-pink-800",
  red: "hover:bg-red-800",
  gray: "hover:bg-gray-800",
  green: "hover:bg-green-800",
  purple: "hover:bg-purple-800",
  indigo: "hover:bg-indigo-800",
  yellow: "hover:bg-yellow-800",
  blue: "hover:bg-blue-800",
};

export interface BadgeProps {
  className?: string;
  name: ReactNode;
  color?: BadgeColor;
  href?: string;
}

export const Badge = ({
  className = "relative",
  name,
  color = "blue",
  href,
}: BadgeProps) => {
  const base = cn(
    "inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
    COLOR_BASE[color],
    className,
  );

  if (href) {
    return (
      <Link
        href={href}
        className={cn(
          "transition-colors duration-300 hover:text-white",
          COLOR_HOVER[color],
          base,
        )}
      >
        {name}
      </Link>
    );
  }

  return <span className={base}>{name}</span>;
};

