import { describe, expect, it } from "vitest";
import {
  formatFeet,
  formatInteger,
  formatMetricNumber,
  formatMoney,
  formatMoneyOrNull,
  formatSqft,
} from "@utils/common/format";

describe("formatMoney", () => {
  it("formats an amount below the default threshold (100) with cents", () => {
    expect(formatMoney(9.99)).toBe("$9.99");
  });

  it("formats an amount at the default threshold without cents", () => {
    expect(formatMoney(100)).toBe("$100");
  });

  it("formats large amounts without cents", () => {
    expect(formatMoney(1_500_000)).toBe("$1,500,000");
  });

  it("formats zero", () => {
    expect(formatMoney(0)).toBe("$0.00");
  });

  it("formats negative amounts", () => {
    expect(formatMoney(-50)).toBe("-$50.00");
  });

  it("respects a custom integerThreshold", () => {
    expect(formatMoney(50, { integerThreshold: 10 })).toBe("$50");
    expect(formatMoney(5, { integerThreshold: 10 })).toBe("$5.00");
  });
});

describe("formatMetricNumber", () => {
  it("formats small numbers with up to 2 decimal places", () => {
    expect(formatMetricNumber(1.5)).toBe("1.5");
    expect(formatMetricNumber(999)).toBe("999");
  });

  it("formats numbers >= 1000 without decimals", () => {
    expect(formatMetricNumber(1_000)).toBe("1,000");
    expect(formatMetricNumber(9_999)).toBe("9,999");
  });

  it("uses compact notation for numbers >= 1,000,000", () => {
    expect(formatMetricNumber(1_000_000)).toBe("1M");
    expect(formatMetricNumber(2_500_000)).toBe("3M");
  });
});

describe("formatInteger", () => {
  it("formats with thousand separators", () => {
    expect(formatInteger(1234567)).toBe("1,234,567");
  });

  it("strips decimal part", () => {
    expect(formatInteger(99.9)).toBe("100");
  });

  it("formats zero", () => {
    expect(formatInteger(0)).toBe("0");
  });
});

describe("formatMoneyOrNull", () => {
  it("returns null for null", () => {
    expect(formatMoneyOrNull(null)).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(formatMoneyOrNull(undefined)).toBeNull();
  });

  it("returns null for NaN", () => {
    expect(formatMoneyOrNull(NaN)).toBeNull();
  });

  it("delegates to formatMoney for valid numbers", () => {
    expect(formatMoneyOrNull(500)).toBe(formatMoney(500));
  });
});

describe("formatSqft", () => {
  it("returns null for null", () => {
    expect(formatSqft(null)).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(formatSqft(undefined)).toBeNull();
  });

  it("returns null for NaN", () => {
    expect(formatSqft(NaN)).toBeNull();
  });

  it("formats with ' sq ft' suffix and rounds", () => {
    expect(formatSqft(2500)).toBe("2,500 sq ft");
    expect(formatSqft(2500.7)).toBe("2,501 sq ft");
  });
});

describe("formatFeet", () => {
  it("returns null for null", () => {
    expect(formatFeet(null)).toBeNull();
  });

  it("returns null for undefined", () => {
    expect(formatFeet(undefined)).toBeNull();
  });

  it("returns null for NaN", () => {
    expect(formatFeet(NaN)).toBeNull();
  });

  it("formats with ' ft' suffix", () => {
    expect(formatFeet(50)).toBe("50 ft");
    expect(formatFeet(0)).toBe("0 ft");
  });
});
