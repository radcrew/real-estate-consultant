import { describe, expect, it } from "vitest";
import { listingLocationLine, listingTitle } from "@utils/listings/headline";
import type { SearchProperty } from "@services/search";

type P = SearchProperty;

const base: P = {
  id: "1",
  address: null,
  city: null,
  state: null,
  country: null,
  latitude: null,
  longitude: null,
  property_type: null,
  listing_type: null,
  description: null,
  size_sqft: null,
  price: null,
  rent: null,
  clear_height: null,
  loading_docks: null,
};

describe("listingTitle", () => {
  it("prefers address when present", () => {
    expect(listingTitle({ ...base, address: "123 Main St" })).toBe("123 Main St");
  });

  it("trims whitespace from address", () => {
    expect(listingTitle({ ...base, address: "  123 Main St  " })).toBe("123 Main St");
  });

  it("falls back to 'city, state' when address is empty", () => {
    expect(listingTitle({ ...base, city: "Austin", state: "TX" })).toBe("Austin, TX");
  });

  it("falls back to city alone when state is missing", () => {
    expect(listingTitle({ ...base, city: "Austin" })).toBe("Austin");
  });

  it("returns 'Property listing' when all location fields are null", () => {
    expect(listingTitle(base)).toBe("Property listing");
  });

  it("ignores a whitespace-only address", () => {
    expect(listingTitle({ ...base, address: "   ", city: "Austin", state: "TX" })).toBe("Austin, TX");
  });
});

describe("listingLocationLine", () => {
  it("joins city, state, country", () => {
    expect(listingLocationLine({ ...base, city: "Austin", state: "TX", country: "US" })).toBe(
      "Austin, TX, US",
    );
  });

  it("omits null parts", () => {
    expect(listingLocationLine({ ...base, city: "Austin", state: "TX" })).toBe("Austin, TX");
  });

  it("returns null when all location fields are null", () => {
    expect(listingLocationLine(base)).toBeNull();
  });
});
