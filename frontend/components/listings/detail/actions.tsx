"use client";

import { useState } from "react";
import { Heart, Share2 } from "lucide-react";

import { cn } from "@utils/common";

/**
 * Listing detail Share + Save row, ported from Voyager's `LikeSaveBtns`.
 * Share uses the Web Share API (falls back to copying the URL); Save is a local
 * toggle (no saved-listings backend yet).
 */
const BTN =
  "flex cursor-pointer items-center rounded-lg px-3 py-1.5 hover:bg-neutral-100 focus:outline-none dark:hover:bg-neutral-800";

export const ListingActions = () => {
  const [saved, setSaved] = useState(false);

  const onShare = async () => {
    if (typeof window === "undefined") {
      return;
    }
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ url });
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(url);
      }
    } catch {
      /* user cancelled / unsupported — ignore */
    }
  };

  return (
    <div className="-mx-3 -my-1.5 flex text-sm text-neutral-700 dark:text-neutral-300">
      <button type="button" className={BTN} onClick={onShare}>
        <Share2 className="size-5" aria-hidden />
        <span className="ml-2.5 hidden sm:block">Share</span>
      </button>
      <button
        type="button"
        className={BTN}
        aria-pressed={saved}
        onClick={() => setSaved((v) => !v)}
      >
        <Heart
          className={cn("size-5", saved && "fill-red-500 text-red-500")}
          aria-hidden
        />
        <span className="ml-2.5 hidden sm:block">{saved ? "Saved" : "Save"}</span>
      </button>
    </div>
  );
};
