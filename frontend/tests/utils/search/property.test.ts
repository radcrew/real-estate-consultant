import { describe, expect, it } from "vitest";
import { mapSearchPropertyMatchToListing } from "@utils/search/property";
import type { SearchPropertyMatch } from "@services/search";

const baseProperty: SearchPropertyMatch["property"] = {
  id: "prop-1",
  address: "100 Commerce Blvd",
  city: "Austin",
  state: "TX",
  country: "US",
  latitude: 30.26,
  longitude: -97.74,
  property_type: "Warehouse",
  listing_type: "For Sale",
  description: "A great warehouse.",
  size_sqft: 10_000,
  price: 1_500_000,
  rent: null,
  clear_height: null,
  loading_docks: null,
  image: "https://example.com/img.jpg",
};

const makeMatch = (
  overrides: Partial<SearchPropertyMatch["property"]> = {},
  score = 87.4,
): SearchPropertyMatch => ({
  property: { ...baseProperty, ...overrides },
  match_score: score,
});

describe("mapSearchPropertyMatchToListing", () => {
  it("maps a fully populated match", () => {
    const result = mapSearchPropertyMatchToListing(makeMatch(), 0);
    expect(result.id).toBe("prop-1");
    expect(result.title).toBe("100 Commerce Blvd");
    expect(result.category).toBe("Warehouse");
    expect(result.transactionType).toBe("For Sale");
    expect(result.location).toBe("Austin · TX · US");
    expect(result.sqftLabel).toBe("10,000 SF");
    expect(result.priceLabel).toBe("$1,500,000");
    expect(result.imageSrc).toBe("https://example.com/img.jpg");
    expect(result.matchScore).toBe(87);
  });

  it("falls back to 'match-{index}' id when property id is null", () => {
    expect(mapSearchPropertyMatchToListing(makeMatch({ id: null }), 3).id).toBe("match-3");
  });

  it("falls back to 'match-{index}' id when property id is whitespace", () => {
    expect(mapSearchPropertyMatchToListing(makeMatch({ id: "  " }), 5).id).toBe("match-5");
  });

  it("falls back title to 'city, state' when address is null", () => {
    const result = mapSearchPropertyMatchToListing(makeMatch({ address: null }), 0);
    expect(result.title).toBe("Austin, TX");
  });

  it("falls back title to property_type when no address or location", () => {
    const result = mapSearchPropertyMatchToListing(
      makeMatch({ address: null, city: null, state: null }),
      0,
    );
    expect(result.title).toBe("Warehouse");
  });

  it("falls back title to 'Property' when all fields are null", () => {
    const result = mapSearchPropertyMatchToListing(
      makeMatch({ address: null, city: null, state: null, property_type: null }),
      0,
    );
    expect(result.title).toBe("Property");
  });

  it("returns '—' for sqftLabel when size_sqft is null", () => {
    expect(mapSearchPropertyMatchToListing(makeMatch({ size_sqft: null }), 0).sqftLabel).toBe("—");
  });

  it("builds a combined price label when both price and rent are present", () => {
    const result = mapSearchPropertyMatchToListing(makeMatch({ rent: 120_000 }), 0);
    expect(result.priceLabel).toBe("$1,500,000 · $120,000/yr rent");
  });

  it("returns rent-only label when price is null", () => {
    const result = mapSearchPropertyMatchToListing(makeMatch({ price: null, rent: 96_000 }), 0);
    expect(result.priceLabel).toBe("$96,000/yr");
  });

  it("returns null priceLabel when both price and rent are null", () => {
    expect(
      mapSearchPropertyMatchToListing(makeMatch({ price: null, rent: null }), 0).priceLabel,
    ).toBeNull();
  });

  it("truncates descriptions longer than 160 chars with ellipsis", () => {
    const long = "x".repeat(200);
    const result = mapSearchPropertyMatchToListing(makeMatch({ description: long }), 0);
    expect(result.matchBlurb).toHaveLength(158); // 157 chars + '…'
    expect(result.matchBlurb.endsWith("…")).toBe(true);
  });

  it("does not truncate descriptions of exactly 160 chars", () => {
    const exact = "y".repeat(160);
    expect(mapSearchPropertyMatchToListing(makeMatch({ description: exact }), 0).matchBlurb).toBe(exact);
  });

  it("returns fallback blurb when description is null", () => {
    expect(
      mapSearchPropertyMatchToListing(makeMatch({ description: null }), 0).matchBlurb,
    ).toBe("Matched from your search profile.");
  });

  it("rounds match_score", () => {
    expect(mapSearchPropertyMatchToListing(makeMatch({}, 92.6), 0).matchScore).toBe(93);
  });

  it("uses empty string for imageSrc when image is undefined", () => {
    const { image: _removed, ...noImage } = baseProperty;
    expect(
      mapSearchPropertyMatchToListing({ property: noImage, match_score: 80 }, 0).imageSrc,
    ).toBe("");
  });
});
