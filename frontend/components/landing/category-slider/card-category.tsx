"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { cn } from "@utils/common";
import { searchService } from "@services/search";

import type { Category } from "./data";

export type CardType = "card4" | "card5";

type CardCategoryProps = {
  category: Category;
  cardType: CardType;
};

export const CardCategory = ({ category, cardType }: CardCategoryProps) => {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const isCard4 = cardType === "card4";

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const { search_profile_id } = await searchService.quickSearch(category.search);
      router.push(`/search/${search_profile_id}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="flex w-full flex-col text-left disabled:opacity-60"
    >
      <div className="group relative aspect-[4/3] w-full flex-shrink-0 overflow-hidden rounded-2xl">
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
      </div>
    </button>
  );
};
