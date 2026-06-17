import { describe, expect, it } from "vitest";
import { mapsHref } from "@utils/listings/maps";

describe("mapsHref", () => {
  it("returns null when lat is null", () => {
    expect(mapsHref(null, -73.9857)).toBeNull();
  });

  it("returns null when lng is null", () => {
    expect(mapsHref(40.7484, null)).toBeNull();
  });

  it("returns null when both are null", () => {
    expect(mapsHref(null, null)).toBeNull();
  });

  it("builds a Google Maps search URL for valid coordinates", () => {
    expect(mapsHref(40.7484, -73.9857)).toBe(
      "https://www.google.com/maps/search/?api=1&query=40.7484,-73.9857",
    );
  });

  it("handles zero coordinates", () => {
    expect(mapsHref(0, 0)).toBe(
      "https://www.google.com/maps/search/?api=1&query=0,0",
    );
  });
});
