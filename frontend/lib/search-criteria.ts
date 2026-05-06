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

/**
 * Parses one criterion from search ``criteria[key]``.
 * Supports full payloads with ``data`` and layout-only rows with ``{ type, label? }`` (no ``data``),
 * using empty values so filter UI still renders.
 */
export const parseCriterionField = (raw: unknown): SearchCriterionField | null => {
  if (!isRecord(raw)) {
    return null;
  }
  const criterionLabel = parseCriterionLabel(raw);
  const labelExtra = criterionLabel != null ? { label: criterionLabel } : {};
  const t = raw.type;

  if (t === "range") {
    const dataRaw = raw.data;
    if (isRecord(dataRaw)) {
      const min = Number(dataRaw.min);
      const max = Number(dataRaw.max);
      if (Number.isFinite(min) && Number.isFinite(max)) {
        return { type: "range", data: { min, max }, ...labelExtra };
      }
    }
    return { type: "range", data: { min: Number.NaN, max: Number.NaN }, ...labelExtra };
  }
  if (t === "location") {
    const d = raw.data;
    if (typeof d === "string") {
      return { type: "location", data: d, ...labelExtra };
    }
    return { type: "location", data: "", ...labelExtra };
  }
  if (t === "multi-select") {
    const d = raw.data;
    if (Array.isArray(d) && d.every((x) => typeof x === "string")) {
      return { type: "multi-select", data: [...d], ...labelExtra };
    }
    return { type: "multi-select", data: [], ...labelExtra };
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

/** Flatten criterion objects into grouped answer payload for criteria update API. */
export const toCriteriaAnswers = (
  fields: Record<string, SearchCriterionField>,
): Record<string, unknown> => {
  const payload: Record<string, unknown> = {};
  for (const [key, field] of Object.entries(fields)) {
    if (field.type === "location") {
      const v = field.data.trim();
      if (v.length > 0) {
        payload[key] = v;
      }
      continue;
    }
    if (field.type === "range") {
      if (Number.isFinite(field.data.min) && Number.isFinite(field.data.max)) {
        payload[key] = { min: field.data.min, max: field.data.max };
      }
      continue;
    }
    if (field.type === "multi-select" && field.data.length > 0) {
      payload[key] = [...field.data];
    }
  }
  return payload;
};