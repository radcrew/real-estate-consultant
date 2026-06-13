export type RangeCriterionData = {
  min: number;
  max: number;
};

export type RangeCriterion = {
  type: "range";
  data: RangeCriterionData;
  label?: string;
  unit?: string;
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

const parseCriterionUnit = (raw: Record<string, unknown>): string | undefined => {
  const v = raw.unit;
  return typeof v === "string" && v.trim().length > 0 ? v.trim() : undefined;
};

const parseRangeBound = (value: unknown): number => {
  if (value === null || value === undefined || value === "") {
    return Number.NaN;
  }
  const n = Number(value);
  return Number.isFinite(n) ? n : Number.NaN;
};

const locationDataToString = (value: unknown): string => {
  if (typeof value === "string") {
    return value.trim();
  }
  if (isRecord(value)) {
    const parts = [value.city, value.state, value.country].filter(
      (part): part is string => typeof part === "string" && part.trim().length > 0,
    );
    if (parts.length > 0) {
      return parts.join(", ");
    }
    if (typeof value.label === "string" && value.label.trim().length > 0) {
      return value.label.trim();
    }
    if (typeof value.input === "string" && value.input.trim().length > 0) {
      return value.input.trim();
    }
  }
  return "";
};

const multiSelectDataToArray = (value: unknown): string[] => {
  if (Array.isArray(value) && value.every((x) => typeof x === "string")) {
    return value.map((x) => x.trim()).filter((x) => x.length > 0);
  }
  if (typeof value === "string" && value.trim().length > 0) {
    return [value.trim()];
  }
  return [];
};

const parseCriterionField = (raw: unknown): SearchCriterionField | null => {
  if (!isRecord(raw)) {
    return null;
  }
  const criterionLabel = parseCriterionLabel(raw);
  const labelExtra = criterionLabel != null ? { label: criterionLabel } : {};
  const type = raw.type;

  if (type === "range") {
    const unit = parseCriterionUnit(raw);
    const unitExtra = unit != null ? { unit } : {};
    const dataRaw = raw.data;
    if (isRecord(dataRaw)) {
      const min = parseRangeBound(dataRaw.min);
      const max = parseRangeBound(dataRaw.max);
      return { type: "range", data: { min, max }, ...labelExtra, ...unitExtra };
    }
    return { type: "range", data: { min: Number.NaN, max: Number.NaN }, ...labelExtra, ...unitExtra };
  }
  if (type === "location") {
    return { type: "location", data: locationDataToString(raw.data), ...labelExtra };
  }
  if (type === "multi-select") {
    return { type: "multi-select", data: multiSelectDataToArray(raw.data), ...labelExtra };
  }
  return null;
};

const EMPTY_RANGE_DATA = { min: Number.NaN, max: Number.NaN };

export const buildDefaultSearchCriteriaShell = (): Record<string, unknown> => ({
  location: { type: "location", label: "Location", data: "" },
  property_type: { type: "multi-select", label: "Property type", data: [] as string[] },
  price: { type: "range", label: "Price", unit: "USD", data: { ...EMPTY_RANGE_DATA } },
  size_sqft: { type: "range", label: "Size", unit: "SF", data: { ...EMPTY_RANGE_DATA } },
});

export const parseSearchCriteriaEntries = (criteria: Record<string, unknown>): ParsedCriteriaEntry[] =>
  Object.entries(criteria)
    .map(([key, value]) => {
      const field = parseCriterionField(value);
      return field ? { key, field } : null;
    })
    .filter((x): x is ParsedCriteriaEntry => x != null);

export const formatCriteriaValue = (value: unknown): string => {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number") return value.toLocaleString();
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if ("label" in obj && obj.label) return String(obj.label);
    if ("min" in obj || "max" in obj) {
      const min = obj.min != null ? Number(obj.min).toLocaleString() : null;
      const max = obj.max != null ? Number(obj.max).toLocaleString() : null;
      if (min && max) return `${min} – ${max}`;
      if (min) return `≥ ${min}`;
      if (max) return `≤ ${max}`;
    }
    return JSON.stringify(value);
  }
  return String(value);
};

export const getCriteriaFromFilters = (
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
      const { min, max } = field.data;
      const hasMin = Number.isFinite(min);
      const hasMax = Number.isFinite(max);
      const hasAnyBound = hasMin || hasMax;
      const hasValidPair = !hasMin || !hasMax || min <= max;

      if (hasAnyBound && hasValidPair) {
        const body: Record<string, unknown> = {};
        if (hasMin) {
          body.min = min;
        }
        if (hasMax) {
          body.max = max;
        }
        if (field.unit != null && field.unit.trim().length > 0) {
          body.unit = field.unit.trim();
        }
        payload[key] = body;
      }
      continue;
    }
    if (field.type === "multi-select" && field.data.length > 0) {
      payload[key] = [...field.data];
    }
  }
  return payload;
};
