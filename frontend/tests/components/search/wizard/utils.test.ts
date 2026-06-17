import { describe, expect, it } from "vitest";
import {
  formatAnswerForSummary,
  getDefaultAnswer,
  getQuestionInputDisplayTitle,
  isQuestionComplete,
  parseQuestion,
} from "@components/search/wizard/utils";
import type {
  LocationQuestion,
  MultiSelectQuestion,
  RangeQuestion,
  TextQuestion,
  WizardQuestion,
} from "@components/search/wizard/types";
import type { IntakeSessionQuestion } from "@services/intake-sessions";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const multiQ: MultiSelectQuestion = {
  id: "property_type",
  kind: "multi-select",
  title: "Property type",
  description: "Select all that apply",
  required: true,
  options: [
    { label: "Warehouse", value: "warehouse" },
    { label: "Office", value: "office" },
  ],
};

const rangeQ: RangeQuestion = {
  id: "price",
  kind: "range",
  title: "Price",
  description: "Enter a range",
  required: true,
  options: { unit: "USD" },
};

const rangeSizeQ: RangeQuestion = {
  id: "size",
  kind: "range",
  title: "Size",
  description: "In sq ft",
  required: true,
  options: { unit: "SF" },
};

const locQ: LocationQuestion = {
  id: "location",
  kind: "location",
  title: "Location",
  description: "Where?",
  required: true,
};

const textQ: TextQuestion = {
  id: "notes",
  kind: "text",
  title: "Notes",
  description: "Any notes?",
  required: true,
};

// ---------------------------------------------------------------------------
// getQuestionInputDisplayTitle
// ---------------------------------------------------------------------------

describe("getQuestionInputDisplayTitle", () => {
  it("appends unit in parentheses for range questions with a unit", () => {
    expect(getQuestionInputDisplayTitle(rangeQ)).toBe("Price (USD)");
  });

  it("trims the unit string", () => {
    const q: RangeQuestion = { ...rangeQ, options: { unit: "  SF  " } };
    expect(getQuestionInputDisplayTitle(q)).toBe("Price (SF)");
  });

  it("returns plain title for range question without unit", () => {
    const q: RangeQuestion = { ...rangeQ, options: undefined };
    expect(getQuestionInputDisplayTitle(q)).toBe("Price");
  });

  it("returns plain title for non-range questions", () => {
    expect(getQuestionInputDisplayTitle(textQ)).toBe("Notes");
    expect(getQuestionInputDisplayTitle(multiQ)).toBe("Property type");
    expect(getQuestionInputDisplayTitle(locQ)).toBe("Location");
  });
});

// ---------------------------------------------------------------------------
// parseQuestion
// ---------------------------------------------------------------------------

const makeRaw = (overrides: Partial<IntakeSessionQuestion>): IntakeSessionQuestion => ({
  key: "q1",
  title: "Q1",
  text: "Describe it",
  type: "text",
  ...overrides,
});

describe("parseQuestion", () => {
  it("parses a multi-select question with array options", () => {
    const q = parseQuestion(makeRaw({
      type: "multi-select",
      options: [{ label: "Warehouse", value: "warehouse" }],
    }));
    expect(q.kind).toBe("multi-select");
    if (q.kind === "multi-select") {
      expect(q.options).toEqual([{ label: "Warehouse", value: "warehouse" }]);
    }
  });

  it("defaults multi-select options to [] when options is not an array", () => {
    const q = parseQuestion(makeRaw({ type: "multi-select", options: undefined }));
    if (q.kind === "multi-select") {
      expect(q.options).toEqual([]);
    }
  });

  it("parses a range question with record options", () => {
    const q = parseQuestion(makeRaw({ type: "range", options: { unit: "USD" } }));
    expect(q.kind).toBe("range");
    if (q.kind === "range") {
      expect(q.options).toEqual({ unit: "USD" });
    }
  });

  it("omits options for range question when options is null", () => {
    const q = parseQuestion(makeRaw({ type: "range", options: undefined }));
    if (q.kind === "range") {
      expect(q.options).toBeUndefined();
    }
  });

  it("parses a location question", () => {
    expect(parseQuestion(makeRaw({ type: "location" })).kind).toBe("location");
  });

  it("defaults unknown types to text", () => {
    expect(parseQuestion(makeRaw({ type: "freeform" as never })).kind).toBe("text");
  });

  it("sets required: true on all parsed questions", () => {
    expect(parseQuestion(makeRaw({ type: "text" })).required).toBe(true);
  });

  it("maps key → id, title, text → description", () => {
    const q = parseQuestion(makeRaw({ key: "loc", title: "Location", text: "Where?" }));
    expect(q.id).toBe("loc");
    expect(q.title).toBe("Location");
    expect(q.description).toBe("Where?");
  });
});

// ---------------------------------------------------------------------------
// formatAnswerForSummary
// ---------------------------------------------------------------------------

describe("formatAnswerForSummary", () => {
  describe("multi-select", () => {
    it("joins labels for selected values", () => {
      expect(formatAnswerForSummary(multiQ, ["warehouse", "office"])).toBe("Warehouse, Office");
    });

    it("filters out unrecognised values", () => {
      expect(formatAnswerForSummary(multiQ, ["warehouse", "unknown"])).toBe("Warehouse");
    });

    it("returns 'Not answered' for empty selection", () => {
      expect(formatAnswerForSummary(multiQ, [])).toBe("Not answered");
    });

    it("returns 'Not answered' for non-array answer", () => {
      expect(formatAnswerForSummary(multiQ, "warehouse")).toBe("Not answered");
    });
  });

  describe("range", () => {
    it("formats price range with USD prefix", () => {
      expect(formatAnswerForSummary(rangeQ, { min: 100_000, max: 500_000 })).toBe(
        "$100,000 - $500,000",
      );
    });

    it("formats size range with unit suffix", () => {
      expect(formatAnswerForSummary(rangeSizeQ, { min: 1_000, max: 5_000 })).toBe(
        "1,000 SF - 5,000 SF",
      );
    });

    it("returns 'Not answered' when min or max are null", () => {
      expect(formatAnswerForSummary(rangeQ, { min: null, max: null })).toBe("Not answered");
    });

    it("returns 'Not answered' for non-object answer", () => {
      expect(formatAnswerForSummary(rangeQ, "bad")).toBe("Not answered");
    });
  });

  describe("location", () => {
    it("returns trimmed string answer", () => {
      expect(formatAnswerForSummary(locQ, "  Austin, TX  ")).toBe("Austin, TX");
    });

    it("joins city, state, country from object", () => {
      expect(formatAnswerForSummary(locQ, { city: "Austin", state: "TX", country: "US" })).toBe(
        "Austin, TX, US",
      );
    });

    it("falls back to label from object", () => {
      expect(formatAnswerForSummary(locQ, { label: "Downtown Austin" })).toBe("Downtown Austin");
    });

    it("falls back to input from object", () => {
      expect(formatAnswerForSummary(locQ, { input: "Austin area" })).toBe("Austin area");
    });

    it("returns 'Not answered' for empty string", () => {
      expect(formatAnswerForSummary(locQ, "")).toBe("Not answered");
    });

    it("returns 'Not answered' for empty object", () => {
      expect(formatAnswerForSummary(locQ, {})).toBe("Not answered");
    });
  });

  describe("text", () => {
    it("returns the string answer", () => {
      expect(formatAnswerForSummary(textQ, "Some notes")).toBe("Some notes");
    });

    it("returns 'Not answered' for empty string", () => {
      expect(formatAnswerForSummary(textQ, "  ")).toBe("Not answered");
    });
  });
});

// ---------------------------------------------------------------------------
// getDefaultAnswer
// ---------------------------------------------------------------------------

describe("getDefaultAnswer", () => {
  it("returns [] for multi-select", () => {
    expect(getDefaultAnswer(multiQ)).toEqual([]);
  });

  it("returns {min:null, max:null} for range", () => {
    expect(getDefaultAnswer(rangeQ)).toEqual({ min: null, max: null });
  });

  it("returns empty string for text", () => {
    expect(getDefaultAnswer(textQ)).toBe("");
  });

  it("returns empty string for location", () => {
    expect(getDefaultAnswer(locQ)).toBe("");
  });
});

// ---------------------------------------------------------------------------
// isQuestionComplete
// ---------------------------------------------------------------------------

describe("isQuestionComplete", () => {
  it("returns true for optional questions regardless of answer", () => {
    const optional: TextQuestion = { ...textQ, required: false };
    expect(isQuestionComplete(optional, "")).toBe(true);
    expect(isQuestionComplete(optional, undefined)).toBe(true);
  });

  describe("multi-select", () => {
    it("returns true when at least one item selected", () => {
      expect(isQuestionComplete(multiQ, ["warehouse"])).toBe(true);
    });

    it("returns false for empty array", () => {
      expect(isQuestionComplete(multiQ, [])).toBe(false);
    });

    it("returns false for non-array answer", () => {
      expect(isQuestionComplete(multiQ, "warehouse")).toBe(false);
    });
  });

  describe("range", () => {
    it("returns true when min <= max", () => {
      expect(isQuestionComplete(rangeQ, { min: 100, max: 500 })).toBe(true);
    });

    it("returns true when min === max", () => {
      expect(isQuestionComplete(rangeQ, { min: 100, max: 100 })).toBe(true);
    });

    it("returns false when min > max", () => {
      expect(isQuestionComplete(rangeQ, { min: 500, max: 100 })).toBe(false);
    });

    it("returns false when min or max is null", () => {
      expect(isQuestionComplete(rangeQ, { min: null, max: 500 })).toBe(false);
      expect(isQuestionComplete(rangeQ, { min: 100, max: null })).toBe(false);
    });

    it("returns false for non-object answer", () => {
      expect(isQuestionComplete(rangeQ, "100-500")).toBe(false);
    });
  });

  describe("location", () => {
    it("returns true for a non-empty string", () => {
      expect(isQuestionComplete(locQ, "Austin, TX")).toBe(true);
    });

    it("returns false for an empty string", () => {
      expect(isQuestionComplete(locQ, "  ")).toBe(false);
    });

    it("returns true for object with city", () => {
      expect(isQuestionComplete(locQ, { city: "Austin" })).toBe(true);
    });

    it("returns true for object with label", () => {
      expect(isQuestionComplete(locQ, { label: "Downtown" })).toBe(true);
    });

    it("returns true for object with input", () => {
      expect(isQuestionComplete(locQ, { input: "Austin area" })).toBe(true);
    });

    it("returns false for empty object", () => {
      expect(isQuestionComplete(locQ, {})).toBe(false);
    });
  });

  describe("text", () => {
    it("returns true for a non-empty string", () => {
      expect(isQuestionComplete(textQ, "hello")).toBe(true);
    });

    it("returns false for empty or whitespace-only string", () => {
      expect(isQuestionComplete(textQ, "")).toBe(false);
      expect(isQuestionComplete(textQ, "   ")).toBe(false);
    });
  });
});
