import { describe, expect, it } from "vitest";
import {
  buildDefaultSearchCriteriaShell,
  formatCriteriaValue,
  getCriteriaFromFilters,
  parseSearchCriteriaEntries,
} from "@utils/search/criteria";
import type { LocationCriterion, MultiSelectCriterion, RangeCriterion } from "@utils/search/criteria";

// ---------------------------------------------------------------------------
// buildDefaultSearchCriteriaShell
// ---------------------------------------------------------------------------

describe("buildDefaultSearchCriteriaShell", () => {
  it("returns an object with the four expected keys", () => {
    const shell = buildDefaultSearchCriteriaShell();
    expect(Object.keys(shell)).toEqual(["location", "property_type", "price", "size_sqft"]);
  });

  it("location entry has empty string data", () => {
    const shell = buildDefaultSearchCriteriaShell() as Record<string, { data: unknown }>;
    expect((shell.location as { data: string }).data).toBe("");
  });

  it("range entries start with NaN bounds", () => {
    const shell = buildDefaultSearchCriteriaShell() as Record<
      string,
      { data: { min: number; max: number } }
    >;
    expect(Number.isNaN(shell.price.data.min)).toBe(true);
    expect(Number.isNaN(shell.price.data.max)).toBe(true);
  });

  it("returns independent objects on each call (no shared references)", () => {
    const a = buildDefaultSearchCriteriaShell() as Record<string, { data: object }>;
    const b = buildDefaultSearchCriteriaShell() as Record<string, { data: object }>;
    expect(a.price.data).not.toBe(b.price.data);
  });
});

// ---------------------------------------------------------------------------
// parseSearchCriteriaEntries
// ---------------------------------------------------------------------------

describe("parseSearchCriteriaEntries", () => {
  it("returns an empty array for an empty object", () => {
    expect(parseSearchCriteriaEntries({})).toEqual([]);
  });

  it("skips entries with unrecognized or missing type", () => {
    const result = parseSearchCriteriaEntries({
      weird: { type: "unknown", data: "x" },
      noType: { data: "y" },
    });
    expect(result).toHaveLength(0);
  });

  it("skips non-object entries", () => {
    expect(parseSearchCriteriaEntries({ foo: "bar", num: 42 })).toHaveLength(0);
  });

  it("parses a location criterion", () => {
    const [entry] = parseSearchCriteriaEntries({
      location: { type: "location", label: "Location", data: "Austin, TX" },
    });
    expect(entry.key).toBe("location");
    expect(entry.field.type).toBe("location");
    expect((entry.field as LocationCriterion).data).toBe("Austin, TX");
    expect(entry.field.label).toBe("Location");
  });

  it("parses a location criterion from an object with city/state/country", () => {
    const [entry] = parseSearchCriteriaEntries({
      location: { type: "location", data: { city: "Austin", state: "TX", country: "US" } },
    });
    expect((entry.field as LocationCriterion).data).toBe("Austin, TX, US");
  });

  it("parses a location criterion from an object using label fallback", () => {
    const [entry] = parseSearchCriteriaEntries({
      location: { type: "location", data: { label: "Downtown Austin" } },
    });
    expect((entry.field as LocationCriterion).data).toBe("Downtown Austin");
  });

  it("parses a location criterion from an object using input fallback", () => {
    const [entry] = parseSearchCriteriaEntries({
      location: { type: "location", data: { input: "Austin area" } },
    });
    expect((entry.field as LocationCriterion).data).toBe("Austin area");
  });

  it("parses a range criterion with finite bounds", () => {
    const [entry] = parseSearchCriteriaEntries({
      price: { type: "range", label: "Price", unit: "USD", data: { min: 100_000, max: 500_000 } },
    });
    expect(entry.field.type).toBe("range");
    const f = entry.field as RangeCriterion;
    expect(f.data.min).toBe(100_000);
    expect(f.data.max).toBe(500_000);
    expect(f.unit).toBe("USD");
    expect(f.label).toBe("Price");
  });

  it("parses range bounds from string numbers", () => {
    const [entry] = parseSearchCriteriaEntries({
      size: { type: "range", data: { min: "200", max: "1000" } },
    });
    const f = entry.field as RangeCriterion;
    expect(f.data.min).toBe(200);
    expect(f.data.max).toBe(1000);
  });

  it("produces NaN bounds for null/empty range data", () => {
    const [entry] = parseSearchCriteriaEntries({
      price: { type: "range", data: { min: null, max: "" } },
    });
    const f = entry.field as RangeCriterion;
    expect(Number.isNaN(f.data.min)).toBe(true);
    expect(Number.isNaN(f.data.max)).toBe(true);
  });

  it("produces NaN bounds when range data key is missing entirely", () => {
    const [entry] = parseSearchCriteriaEntries({ price: { type: "range" } });
    const f = entry.field as RangeCriterion;
    expect(Number.isNaN(f.data.min)).toBe(true);
    expect(Number.isNaN(f.data.max)).toBe(true);
  });

  it("parses a multi-select criterion from an array", () => {
    const [entry] = parseSearchCriteriaEntries({
      property_type: { type: "multi-select", label: "Type", data: ["Warehouse", "Office"] },
    });
    const f = entry.field as MultiSelectCriterion;
    expect(f.data).toEqual(["Warehouse", "Office"]);
    expect(f.label).toBe("Type");
  });

  it("parses a multi-select criterion from a single string", () => {
    const [entry] = parseSearchCriteriaEntries({
      property_type: { type: "multi-select", data: "Retail" },
    });
    expect((entry.field as MultiSelectCriterion).data).toEqual(["Retail"]);
  });

  it("trims whitespace from multi-select entries and drops blanks", () => {
    const [entry] = parseSearchCriteriaEntries({
      property_type: { type: "multi-select", data: ["  Warehouse  ", "", "  "] },
    });
    expect((entry.field as MultiSelectCriterion).data).toEqual(["Warehouse"]);
  });

  it("returns empty array for multi-select with non-string-array data", () => {
    const [entry] = parseSearchCriteriaEntries({
      property_type: { type: "multi-select", data: [1, 2, 3] },
    });
    expect((entry.field as MultiSelectCriterion).data).toEqual([]);
  });

  it("omits label when it is empty or whitespace-only", () => {
    const [entry] = parseSearchCriteriaEntries({
      location: { type: "location", label: "  ", data: "Austin" },
    });
    expect(entry.field.label).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// formatCriteriaValue
// ---------------------------------------------------------------------------

describe("formatCriteriaValue", () => {
  it("returns '—' for null", () => {
    expect(formatCriteriaValue(null)).toBe("—");
  });

  it("returns '—' for undefined", () => {
    expect(formatCriteriaValue(undefined)).toBe("—");
  });

  it("returns the string as-is", () => {
    expect(formatCriteriaValue("Austin, TX")).toBe("Austin, TX");
  });

  it("formats a number with locale separators", () => {
    expect(formatCriteriaValue(1_500_000)).toBe("1,500,000");
  });

  it("joins an array with ', '", () => {
    expect(formatCriteriaValue(["Warehouse", "Office"])).toBe("Warehouse, Office");
  });

  it("uses label property when present on an object", () => {
    expect(formatCriteriaValue({ label: "Downtown Austin", city: "Austin" })).toBe("Downtown Austin");
  });

  it("formats a min–max range object", () => {
    expect(formatCriteriaValue({ min: 100_000, max: 500_000 })).toBe("100,000 – 500,000");
  });

  it("formats a min-only range as '≥ min'", () => {
    expect(formatCriteriaValue({ min: 100_000 })).toBe("≥ 100,000");
  });

  it("formats a max-only range as '≤ max'", () => {
    expect(formatCriteriaValue({ max: 500_000 })).toBe("≤ 500,000");
  });

  it("falls back to JSON.stringify for unrecognized objects", () => {
    expect(formatCriteriaValue({ foo: "bar" })).toBe('{"foo":"bar"}');
  });
});

// ---------------------------------------------------------------------------
// getCriteriaFromFilters
// ---------------------------------------------------------------------------

describe("getCriteriaFromFilters", () => {
  it("returns an empty object for empty input", () => {
    expect(getCriteriaFromFilters({})).toEqual({});
  });

  it("includes a non-empty location value", () => {
    const loc: LocationCriterion = { type: "location", data: "Austin, TX" };
    expect(getCriteriaFromFilters({ location: loc })).toEqual({ location: "Austin, TX" });
  });

  it("omits a location when data is empty or whitespace", () => {
    expect(getCriteriaFromFilters({ location: { type: "location", data: "" } })).toEqual({});
    expect(getCriteriaFromFilters({ location: { type: "location", data: "  " } })).toEqual({});
  });

  it("includes a range with both finite bounds", () => {
    const range: RangeCriterion = { type: "range", unit: "USD", data: { min: 100_000, max: 500_000 } };
    expect(getCriteriaFromFilters({ price: range })).toEqual({
      price: { min: 100_000, max: 500_000, unit: "USD" },
    });
  });

  it("includes a range with only a min bound", () => {
    const range: RangeCriterion = { type: "range", data: { min: 50_000, max: NaN } };
    expect(getCriteriaFromFilters({ price: range })).toEqual({ price: { min: 50_000 } });
  });

  it("includes a range with only a max bound", () => {
    const range: RangeCriterion = { type: "range", data: { min: NaN, max: 200_000 } };
    expect(getCriteriaFromFilters({ price: range })).toEqual({ price: { max: 200_000 } });
  });

  it("omits a range when both bounds are NaN", () => {
    const range: RangeCriterion = { type: "range", data: { min: NaN, max: NaN } };
    expect(getCriteriaFromFilters({ price: range })).toEqual({});
  });

  it("omits a range when min > max (invalid pair)", () => {
    const range: RangeCriterion = { type: "range", data: { min: 500_000, max: 100_000 } };
    expect(getCriteriaFromFilters({ price: range })).toEqual({});
  });

  it("omits unit from range when unit is empty or whitespace", () => {
    const range: RangeCriterion = { type: "range", unit: "  ", data: { min: 10, max: 20 } };
    const result = getCriteriaFromFilters({ size: range }) as Record<string, Record<string, unknown>>;
    expect(result.size.unit).toBeUndefined();
  });

  it("includes a non-empty multi-select value", () => {
    const ms: MultiSelectCriterion = { type: "multi-select", data: ["Warehouse", "Office"] };
    expect(getCriteriaFromFilters({ property_type: ms })).toEqual({
      property_type: ["Warehouse", "Office"],
    });
  });

  it("omits a multi-select with empty array", () => {
    const ms: MultiSelectCriterion = { type: "multi-select", data: [] };
    expect(getCriteriaFromFilters({ property_type: ms })).toEqual({});
  });

  it("returns a copy of the multi-select array (not the same reference)", () => {
    const data = ["Warehouse"];
    const ms: MultiSelectCriterion = { type: "multi-select", data };
    const result = getCriteriaFromFilters({ property_type: ms });
    expect(result.property_type).not.toBe(data);
  });
});
