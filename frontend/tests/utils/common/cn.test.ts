import { describe, expect, it } from "vitest";
import { cn } from "@utils/common/cn";

describe("cn", () => {
  it("returns an empty string for no arguments", () => {
    expect(cn()).toBe("");
  });

  it("joins multiple class strings", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("ignores falsy values", () => {
    expect(cn("foo", false, undefined, null, "bar")).toBe("foo bar");
  });

  it("resolves conflicting Tailwind utilities (last wins)", () => {
    expect(cn("p-4", "p-8")).toBe("p-8");
  });

  it("keeps non-conflicting utilities", () => {
    expect(cn("text-sm", "font-bold")).toBe("text-sm font-bold");
  });

  it("handles conditional object syntax from clsx", () => {
    expect(cn({ "text-red-500": true, "text-blue-500": false })).toBe("text-red-500");
  });
});
