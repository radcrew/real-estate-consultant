/** Display chips for the search results criteria recap (from API `criteria`, not sessionStorage). */

export type SearchResultsChip = {
  label: string;
  value: string;
};

const humanizeKey = (key: string): string =>
  key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());

const formatCriteriaValue = (value: unknown): string => {
  if (value == null) {
    return "";
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((v) => formatCriteriaValue(v)).filter(Boolean).join(", ");
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
};

/** Build recap chips from intake session ``criteria`` (flat object from API). */
export const chipsFromIntakeCriteria = (criteria: unknown): SearchResultsChip[] => {
  if (!criteria || typeof criteria !== "object" || Array.isArray(criteria)) {
    return [];
  }

  const entries = Object.entries(criteria as Record<string, unknown>);
  const chips: SearchResultsChip[] = [];

  for (const [key, raw] of entries) {
    const value = formatCriteriaValue(raw).trim();
    if (!value) {
      continue;
    }
    chips.push({ label: humanizeKey(key), value });
  }

  return chips;
};
