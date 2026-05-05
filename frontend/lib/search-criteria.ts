export type RangeCriterionData = {
  min: number;
  max: number;
};

export type RangeCriterion = {
  type: "range";
  data: RangeCriterionData;
  /** Display label from API (``criteria[key].label``). */
  label?: string;
};

export type LocationCriterion = {
  type: "location";
  data: string;
  label?: string;
};

export type MultiSelectCriterion = {
  type: "multi-select";
  data: string[];
  label?: string;
};

export type SearchCriterionField = RangeCriterion | LocationCriterion | MultiSelectCriterion;

export type ParsedCriteriaEntry = {
  key: string;
  field: SearchCriterionField;
};

const isRecord = (v: unknown): v is Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v);

const parseCriterionLabel = (raw: Record<string, unknown>): string | undefined => {
  const v = raw.label;
  return typeof v === "string" && v.trim().length > 0 ? v.trim() : undefined;
};

export const parseCriterionField = (raw: unknown): SearchCriterionField | null => {
  if (!isRecord(raw)) {
    return null;
  }
  const criterionLabel = parseCriterionLabel(raw);
  const t = raw.type;
  if (t === "range" && isRecord(raw.data)) {
    const min = Number(raw.data.min);
    const max = Number(raw.data.max);
    if (Number.isFinite(min) && Number.isFinite(max)) {
      return { type: "range", data: { min, max }, ...(criterionLabel != null ? { label: criterionLabel } : {}) };
    }
    return null;
  }
  if (t === "location" && typeof raw.data === "string") {
    return { type: "location", data: raw.data, ...(criterionLabel != null ? { label: criterionLabel } : {}) };
  }
  if (t === "multi-select" && Array.isArray(raw.data) && raw.data.every((x) => typeof x === "string")) {
    return {
      type: "multi-select",
      data: [...raw.data],
      ...(criterionLabel != null ? { label: criterionLabel } : {}),
    };
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