"use client";

import { searchService } from "@services/search";

// Bind once so callers get stable references they can safely list in deps.
const search = searchService.search.bind(searchService);
const updateCriteria = searchService.updateCriteria.bind(searchService);

export const useSearchByProfile = () => ({ search, updateCriteria });
