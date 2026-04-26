import type { LlmExtracted } from "@services/intake-sessions";

export type ExtractedRow = { label: string; value: string };

const formatUsd = (n: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);

const titleCase = (s: string) =>
  s.length ? s[0].toUpperCase() + s.slice(1).toLowerCase() : s;

export const buildExtractedRows = (extracted: LlmExtracted | null): ExtractedRow[] => {
  if (!extracted) {
    return [];
  }
  const rows: ExtractedRow[] = [];
  if (extracted.building_type.length > 0) {
    rows.push({
      label: "Type",
      value: extracted.building_type.map(titleCase).join(", "),
    });
  }
  const { min, max } = extracted.rent_range;
  if (min > 0 || max > 0) {
    rows.push({ label: "Min Budget", value: formatUsd(min) });
    rows.push({ label: "Max Budget", value: formatUsd(max) });
  }
  if (extracted.location?.label?.trim()) {
    rows.push({ label: "Market", value: extracted.location.label });
  }
  const smin = extracted.size_sqft.min;
  const smax = extracted.size_sqft.max;
  if (smin > 0 || smax > 0) {
    rows.push({
      label: "Size",
      value: `${new Intl.NumberFormat("en-US").format(smin)} – ${new Intl.NumberFormat("en-US").format(smax)} SF`,
    });
  }
  return rows;
};
