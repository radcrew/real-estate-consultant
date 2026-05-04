import type { LlmInputResponse } from "@services/intake-sessions";

import type { SearchResultsChip } from "./search-results-chips";

const formatRange = (min: number, max: number, suffix: string): string => {
  if (min === max) {
    return `${min.toLocaleString()}${suffix}`;
  }
  return `${min.toLocaleString()}–${max.toLocaleString()}${suffix}`;
};

/** Turn LLM extracted state into human-readable recap chips for the results page. */
export const chipsFromLlmResponse = (response: LlmInputResponse): SearchResultsChip[] => {
  const chips: SearchResultsChip[] = [];
  const { extracted } = response;

  if (extracted.building_type?.length) {
    chips.push({
      label: "Building type",
      value: extracted.building_type.join(", "),
    });
  }

  if (extracted.location?.label) {
    chips.push({ label: "Location", value: extracted.location.label });
  }

  const { min: sqMin, max: sqMax } = extracted.size_sqft;
  if (sqMin > 0 || sqMax > 0) {
    chips.push({
      label: "Size",
      value: formatRange(sqMin, sqMax, " SF"),
    });
  }

  const { min: rMin, max: rMax } = extracted.rent_range;
  if (rMin > 0 || rMax > 0) {
    const rent =
      rMin === rMax
        ? `$${rMin.toLocaleString()}/mo`
        : `$${rMin.toLocaleString()}–$${rMax.toLocaleString()}/mo`;
    chips.push({ label: "Rent budget", value: rent });
  }

  return chips;
};
