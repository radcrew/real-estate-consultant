import { describe, expect, it } from "vitest";

// Smoke test: verifies the Vitest harness is wired up and runnable.
describe("vitest harness", () => {
  it("runs", () => {
    expect(1 + 1).toBe(2);
  });
});
