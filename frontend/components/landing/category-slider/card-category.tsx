import Link from "next/link";
import Image from "next/image";

import { cn } from "@utils/common";

import type { Category } from "./data";

/**
 * Category card, merging Voyager's `CardCategory4` (square→5:6, centered text)
 * and `CardCategory5` (4:3, left-aligned text) into one variant-driven card.
 */
export type CardType = "card4" | "card5";

type CardCategoryProps = {
  category: Category;
  cardType: CardType;
};

export const CardCategory = ({ category, cardType }: CardCategoryProps) => {
  const isCard4 = cardType === "card4";

  return (
    <Link href={category.href} className="flex flex-col">
      <div
        className={cn(
          "group relative w-full flex-shrink-0 overflow-hidden rounded-2xl",
          isCard4 ? "aspect-square sm:aspect-[5/6]" : "aspect-[4/3]",
        )}
      >
        <Image
          src={category.thumbnail}
          className="size-full rounded-2xl object-cover"
          fill
          alt=""
          aria-hidden
          sizes="(max-width: 400px) 100vw, 400px"
        />
        <span className="absolute inset-0 bg-black/10 opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
      <div className={cn("mt-4 truncate", isCard4 ? "px-2 text-center" : "px-3")}>
        <h2 className="truncate text-base font-medium text-neutral-900 sm:text-lg dark:text-neutral-100">
          {category.name}
        </h2>
        <span className="mt-2 block text-sm text-neutral-500 dark:text-neutral-400">
          {category.count.toLocaleString("en-US")} properties
        </span>
      </div>
    </Link>
  );
};
