"use client";

import { useEffect, useState } from "react";
import { Heart, Share2 } from "lucide-react";

import { isSavedListing, toggleSavedListing } from "@lib/saved-listings";
import { cn } from "@utils/common";

/**
 * Listing detail Share + Save row, ported from Voyager's `LikeSaveBtns`.
 * Share uses the Web Share API (falls back to copying the URL); Save persists in
 * localStorage keyed by listing id, staying in sync with the card hearts.
 */
const BTN =
  "flex cursor-pointer items-center rounded-lg px-3 py-1.5 hover:bg-neutral-100 focus:outline-none dark:hover:bg-neutral-800";

type ListingActionsProps = {
  id?: string;
};

export const ListingActions = ({ id }: ListingActionsProps) => {
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (id) {
      setSaved(isSavedListing(id));
    }
  }, [id]);

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
        onClick={() => setSaved(id ? toggleSavedListing(id) : !saved)}
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
