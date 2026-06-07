"use client";

import { useEffect, useState } from "react";

import { isSavedListing, toggleSavedListing } from "@lib/saved-listings";
import { cn } from "@utils/common";

/**
 * Voyager `BtnLikeIcon` — a heart "save" toggle shown on property cards. Ported
 * from Voyager's component. When `id` is provided the saved state persists in
 * localStorage (no saved-listings backend yet); otherwise it's purely local.
 * Stops click propagation so it works inside a card-wide link.
 */
export interface BtnLikeIconProps {
  className?: string;
  colorClass?: string;
  isLiked?: boolean;
  /** Listing id — when set, the saved state persists across navigation. */
  id?: string;
}

export const BtnLikeIcon = ({
  className,
  colorClass = "text-white bg-black/30 hover:bg-black/50",
  isLiked = false,
  id,
}: BtnLikeIconProps) => {
  const [liked, setLiked] = useState(isLiked);

  useEffect(() => {
    if (id) {
      setLiked(isSavedListing(id));
    }
  }, [id]);

  return (
    <button
      type="button"
      title="Save"
      aria-label={liked ? "Saved" : "Save"}
      aria-pressed={liked}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setLiked(id ? toggleSavedListing(id) : !liked);
      }}
      className={cn(
        "flex size-8 items-center justify-center rounded-full transition-colors focus:outline-none",
        colorClass,
        liked && "text-red-500",
        className,
      )}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="size-5"
        fill={liked ? "currentColor" : "none"}
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
        />
      </svg>
    </button>
  );
};

export default BtnLikeIcon;
