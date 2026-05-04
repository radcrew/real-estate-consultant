"use client";

import { useCallback } from "react";

import { searchService } from "@services/search";

export const useSearchByProfile = () => {
  const search = useCallback(
    searchService.search.bind(searchService),
    [],
  );

  return { search };
};
