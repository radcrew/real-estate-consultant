import type { RankedPropertyListing } from "./mock-data";
import type { ResultsSortOption } from "./results-toolbar";

const parseSqft = (label: string): number => {
  const match = label.replace(/,/g, "").match(/(\d+)/);
  return match ? Number.parseInt(match[1], 10) : 0;
};

export const sortRankedListings = (
  listings: RankedPropertyListing[],
  sortBy: ResultsSortOption,
): RankedPropertyListing[] => {
  const copy = [...listings];

  if (sortBy === "match") {
    copy.sort((a, b) => b.matchScore - a.matchScore);
    return copy;
  }

  if (sortBy === "size") {
    copy.sort((a, b) => parseSqft(b.sqftLabel) - parseSqft(a.sqftLabel));
    return copy;
  }

  copy.sort((a, b) => a.title.localeCompare(b.title));
  return copy;
};
