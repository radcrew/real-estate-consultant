import type { FeaturedListing } from "@constants";
import { FEATURED_LISTINGS } from "@constants";

export type RankedPropertyListing = FeaturedListing & {
  matchScore: number;
  matchBlurb: string;
};

const MATCH_BLURBS = [
  "Strong fit on size, type, and submarket versus your criteria.",
  "Good alignment on rent range; verify dock count on tour.",
  "High match on location; check lease term flexibility with broker.",
  "Solid size and clear height profile for your use case.",
  "Close to target geography; confirm ingress for full trailer fleet.",
  "Meets building type and scale; secondary on parking ratios.",
] as const;

/** Demo ranked listings until a search API exists. */
export const MOCK_RANKED_LISTINGS: RankedPropertyListing[] = FEATURED_LISTINGS.map(
  (listing, index) => ({
    ...listing,
    matchScore: Math.max(58, 96 - index * 5 - (index % 3) * 2),
    matchBlurb: MATCH_BLURBS[index % MATCH_BLURBS.length],
  }),
);
