export type RangeCriterionData = {
  min: number;
  max: number;
};

export type RangeCriterion = {
  type: "range";
  data: RangeCriterionData;
};

export type LocationCriterion = {
  type: "location";
  data: string;
};

export type MultiSelectCriterion = {
  type: "multi-select";
  data: string[];
};

export type SearchCriterionField = RangeCriterion | LocationCriterion | MultiSelectCriterion;

export type ParsedCriteriaEntry = {
  key: string;
  field: SearchCriterionField;
};

const isRecord = (v: unknown): v is Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v);

export const parseCriterionField = (raw: unknown): SearchCriterionField | null => {
  if (!isRecord(raw)) {
    return null;
  }
  const t = raw.type;
  if (t === "range" && isRecord(raw.data)) {
    const min = Number(raw.data.min);
    const max = Number(raw.data.max);
    if (Number.isFinite(min) && Number.isFinite(max)) {
      return { type: "range", data: { min, max } };
    }
    return null;
  }
  if (t === "location" && typeof raw.data === "string") {
    return { type: "location", data: raw.data };
  }
  if (t === "multi-select" && Array.isArray(raw.data) && raw.data.every((x) => typeof x === "string")) {
    return { type: "multi-select", data: [...raw.data] };
  }
  return null;
};

export const parseSearchCriteriaEntries = (criteria: Record<string, unknown>): ParsedCriteriaEntry[] =>
  Object.entries(criteria)
    .map(([key, value]) => {
      const field = parseCriterionField(value);
      return field ? { key, field } : null;
    })
    .filter((x): x is ParsedCriteriaEntry => x != null);

export const humanizeCriteriaKey = (key: string): string =>
  key
    .split("_")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
