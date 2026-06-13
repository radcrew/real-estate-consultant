"use client";

import Image from "next/image";
import { Check } from "lucide-react";
import type { HTMLAttributeReferrerPolicy } from "react";

import { cn } from "@utils/common";

/**
 * Voyager-styled avatar (image or colored initial, optional "checked" badge).
 *
 * Ported from Voyager's `shared/Avatar.tsx`. Decoupled from Voyager config:
 * the `brand`/`contains` imports (DEFAULT_AVATAR, avatarColors) are inlined, the
 * line-awesome check icon is swapped for lucide's `Check`, and `next/image` uses
 * `fill` (Next 16 requires dimensions). Remote avatar hosts must be allowed in
 * next.config `images.remotePatterns`.
 */
const AVATAR_BG_COLORS = [
  "#ef4444",
  "#f59e0b",
  "#10b981",
  "#3b82f6",
  "#6366f1",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
];

export interface AvatarProps {
  containerClassName?: string;
  sizeClass?: string;
  radius?: string;
  imgUrl?: string;
  userName?: string;
  hasChecked?: boolean;
  hasCheckedClass?: string;
  /** Passed to next/image sizes — set to match the rendered pixel size for best quality. */
  sizes?: string;
  /** Skip the image optimizer (needed for arbitrary remote hosts not in next.config). */
  unoptimized?: boolean;
  /** Forwarded to the image (e.g. "no-referrer" for OAuth provider avatars). */
  referrerPolicy?: HTMLAttributeReferrerPolicy;
}

export const Avatar = ({
  containerClassName = "ring-1 ring-white dark:ring-neutral-900",
  sizeClass = "h-6 w-6 text-sm",
  radius = "rounded-full",
  imgUrl,
  userName = "User",
  hasChecked,
  hasCheckedClass = "w-4 h-4 -top-0.5 -right-0.5",
  sizes = "96px",
  unoptimized,
  referrerPolicy,
}: AvatarProps) => {
  const name = userName || "User";
  const bgColor =
    AVATAR_BG_COLORS[name.charCodeAt(0) % AVATAR_BG_COLORS.length];

  return (
    <div
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center font-semibold text-neutral-100 uppercase shadow-inner",
        radius,
        sizeClass,
        containerClassName,
      )}
      style={{ backgroundColor: imgUrl ? undefined : bgColor }}
    >
      {imgUrl && (
        <Image
          className={cn("absolute inset-0 h-full w-full object-cover", radius)}
          src={imgUrl}
          alt={name}
          fill
          sizes={sizes}
          unoptimized={unoptimized}
          referrerPolicy={referrerPolicy}
        />
      )}
      <span>{name[0]}</span>

      {hasChecked && (
        <span
          className={cn(
            "absolute flex items-center justify-center rounded-full bg-teal-500 text-xs text-white",
            hasCheckedClass,
          )}
        >
          <Check className="h-3 w-3" />
        </span>
      )}
    </div>
  );
};

