import { describe, expect, it, vi } from "vitest";
import {
  isRangeInvalid,
  rangePriceSummaryForAria,
  rangePriceTriggerText,
  rangeNormalSummaryForAria,
  rangeNormalTriggerText,
  stopMenuKeyboardCapture,
  stopMenuTriggerBubble,
} from "@components/search/result/filter-bar/filters/utils";

// ---------------------------------------------------------------------------
// stopMenuTriggerBubble
// ---------------------------------------------------------------------------

describe("stopMenuTriggerBubble", () => {
  it("calls preventDefault and stopPropagation", () => {
    const e = { preventDefault: vi.fn(), stopPropagation: vi.fn() };
    stopMenuTriggerBubble(e);
    expect(e.preventDefault).toHaveBeenCalledOnce();
    expect(e.stopPropagation).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// stopMenuKeyboardCapture
// ---------------------------------------------------------------------------

describe("stopMenuKeyboardCapture", () => {
  it("calls stopPropagation", () => {
    const e = { stopPropagation: vi.fn() } as never;
    stopMenuKeyboardCapture(e);
    expect(e.stopPropagation).toHaveBeenCalledOnce();
  });
});

// ---------------------------------------------------------------------------
// isRangeInvalid
// ---------------------------------------------------------------------------

describe("isRangeInvalid", () => {
  it("returns false when both bounds are NaN", () => {
    expect(isRangeInvalid({ min: NaN, max: NaN })).toBe(false);
  });

  it("returns false when min <= max", () => {
    expect(isRangeInvalid({ min: 100, max: 500 })).toBe(false);
    expect(isRangeInvalid({ min: 100, max: 100 })).toBe(false);
  });

  it("returns true when min > max", () => {
    expect(isRangeInvalid({ min: 500, max: 100 })).toBe(true);
  });

  it("returns false when only one bound is finite", () => {
    expect(isRangeInvalid({ min: 100, max: NaN })).toBe(false);
    expect(isRangeInvalid({ min: NaN, max: 500 })).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// rangePriceTriggerText
// ---------------------------------------------------------------------------

describe("rangePriceTriggerText", () => {
  it("formats both bounds with unit prefix", () => {
    expect(rangePriceTriggerText({ min: 100_000, max: 500_000 }, "Price", "USD")).toBe(
      "USD $100,000 – $500,000",
    );
  });

  it("defaults unit prefix to 'USD' when unit is not provided", () => {
    expect(rangePriceTriggerText({ min: 100_000, max: 500_000 }, "Price")).toBe(
      "USD $100,000 – $500,000",
    );
  });

  it("shows 'From' for min-only", () => {
    expect(rangePriceTriggerText({ min: 100_000, max: NaN }, "Price", "USD")).toBe(
      "From $100,000",
    );
  });

  it("shows 'Up to' for max-only", () => {
    expect(rangePriceTriggerText({ min: NaN, max: 500_000 }, "Price", "USD")).toBe(
      "Up to $500,000",
    );
  });

  it("returns 'label (unit)' when no bounds set and unit given", () => {
    expect(rangePriceTriggerText({ min: NaN, max: NaN }, "Price", "USD")).toBe("Price (USD)");
  });

  it("returns plain label when no bounds and no unit", () => {
    expect(rangePriceTriggerText({ min: NaN, max: NaN }, "Price")).toBe("Price");
  });
});

// ---------------------------------------------------------------------------
// rangeNormalTriggerText
// ---------------------------------------------------------------------------

describe("rangeNormalTriggerText", () => {
  it("formats both bounds with unit suffix", () => {
    expect(rangeNormalTriggerText({ min: 1_000, max: 5_000 }, "Size", "SF")).toBe(
      "1,000 – 5,000 SF",
    );
  });

  it("omits suffix when no unit", () => {
    expect(rangeNormalTriggerText({ min: 1_000, max: 5_000 }, "Size")).toBe("1,000 – 5,000");
  });

  it("shows 'From' for min-only", () => {
    expect(rangeNormalTriggerText({ min: 2_000, max: NaN }, "Size", "SF")).toBe("From 2,000 SF");
  });

  it("shows 'Up to' for max-only", () => {
    expect(rangeNormalTriggerText({ min: NaN, max: 5_000 }, "Size", "SF")).toBe("Up to 5,000 SF");
  });

  it("returns 'label (unit)' when no bounds and unit given", () => {
    expect(rangeNormalTriggerText({ min: NaN, max: NaN }, "Size", "SF")).toBe("Size (SF)");
  });

  it("returns plain label when no bounds and no unit", () => {
    expect(rangeNormalTriggerText({ min: NaN, max: NaN }, "Size")).toBe("Size");
  });
});

// ---------------------------------------------------------------------------
// rangePriceSummaryForAria
// ---------------------------------------------------------------------------

describe("rangePriceSummaryForAria", () => {
  it("describes a full range", () => {
    expect(rangePriceSummaryForAria({ min: 100_000, max: 500_000 })).toBe(
      "$100,000 to $500,000",
    );
  });

  it("describes a min-only bound", () => {
    expect(rangePriceSummaryForAria({ min: 100_000, max: NaN })).toBe("minimum $100,000");
  });

  it("describes a max-only bound", () => {
    expect(rangePriceSummaryForAria({ min: NaN, max: 500_000 })).toBe("maximum $500,000");
  });

  it("returns 'Not set' when no bounds", () => {
    expect(rangePriceSummaryForAria({ min: NaN, max: NaN })).toBe("Not set");
  });
});

// ---------------------------------------------------------------------------
// rangeNormalSummaryForAria
// ---------------------------------------------------------------------------

describe("rangeNormalSummaryForAria", () => {
  it("describes a full range with unit", () => {
    expect(rangeNormalSummaryForAria({ min: 1_000, max: 5_000 }, "SF")).toBe(
      "1,000 to 5,000 SF",
    );
  });

  it("describes a min-only bound with unit", () => {
    expect(rangeNormalSummaryForAria({ min: 2_000, max: NaN }, "SF")).toBe("minimum 2,000 SF");
  });

  it("describes a max-only bound", () => {
    expect(rangeNormalSummaryForAria({ min: NaN, max: 5_000 })).toBe("maximum 5,000");
  });

  it("returns 'Not set' when no bounds", () => {
    expect(rangeNormalSummaryForAria({ min: NaN, max: NaN }, "SF")).toBe("Not set");
  });
});
