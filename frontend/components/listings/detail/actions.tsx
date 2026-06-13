"use client";

import { Heart } from "lucide-react";

import { useSavedListings } from "@components/saved/provider";
import { cn } from "@utils/common";

/**
 * Listing detail Save button, ported from Voyager's `LikeSaveBtns`. Backed
 * by the per-user saved-listings API, in sync with the card hearts.
 */
const BTN =
  "flex cursor-pointer items-center rounded-lg px-3 py-1.5 hover:bg-neutral-100 focus:outline-none dark:hover:bg-neutral-800";

type ListingActionsProps = {
  id?: string;
};

export const ListingActions = ({ id }: ListingActionsProps) => {
  const { isSaved, toggle } = useSavedListings();
  const saved = id ? isSaved(id) : false;

  return (
    <div className="-mx-3 -my-1.5 flex text-sm text-neutral-700 dark:text-neutral-300">
      <button
        type="button"
        className={BTN}
        aria-pressed={saved}
        onClick={() => id && toggle(id)}
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
