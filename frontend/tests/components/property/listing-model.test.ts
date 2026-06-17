import { describe, expect, it } from "vitest";
import {
  detailToModel,
  propertyToModel,
  toPropertyModels,
} from "@components/property/listing-model";
import type { SearchProperty, SearchPropertyMatch } from "@services/search";
import type { ListingDetailResponse } from "@services/listings";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const baseProperty: SearchProperty = {
  id: "p-1",
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
  clear_height: 24,
  loading_docks: 4,
  listing_broker_name: "  Jane Doe  ",
  listing_broker_email: "  jane@broker.com  ",
  listing_broker_phone: "  555-0100  ",
  image: "https://example.com/img.jpg",
};

const makeMatch = (overrides: Partial<SearchProperty> = {}, score = 90): SearchPropertyMatch => ({
  property: { ...baseProperty, ...overrides },
  match_score: score,
});

// ---------------------------------------------------------------------------
// propertyToModel
// ---------------------------------------------------------------------------

describe("propertyToModel", () => {
  it("sets href to /listings/{id}", () => {
    expect(propertyToModel(baseProperty).href).toBe("/listings/p-1");
  });

  it("uses match-{index} in href when id is null", () => {
    expect(propertyToModel({ ...baseProperty, id: null }, 3).href).toBe("/listings/match-3");
  });

  it("trims description", () => {
    expect(propertyToModel({ ...baseProperty, description: "  Nice  " }).description).toBe("Nice");
  });

  it("returns null description when property description is null", () => {
    expect(propertyToModel({ ...baseProperty, description: null }).description).toBeNull();
  });

  it("returns null description for whitespace-only description", () => {
    expect(propertyToModel({ ...baseProperty, description: "   " }).description).toBeNull();
  });

  it("wraps image in galleryImgs array", () => {
    expect(propertyToModel(baseProperty).galleryImgs).toEqual(["https://example.com/img.jpg"]);
  });

  it("returns empty galleryImgs when image is null", () => {
    expect(propertyToModel({ ...baseProperty, image: null }).galleryImgs).toEqual([]);
  });

  it("builds map coordinates when lat and lng are finite", () => {
    expect(propertyToModel(baseProperty).map).toEqual({ lat: 30.26, lng: -97.74 });
  });

  it("returns null map when latitude is null", () => {
    expect(propertyToModel({ ...baseProperty, latitude: null }).map).toBeNull();
  });

  it("returns null map when longitude is null", () => {
    expect(propertyToModel({ ...baseProperty, longitude: null }).map).toBeNull();
  });

  it("includes mapsHref for valid coordinates", () => {
    expect(propertyToModel(baseProperty).mapsHref).toContain("30.26");
  });

  it("returns null mapsHref when coordinates are missing", () => {
    expect(propertyToModel({ ...baseProperty, latitude: null }).mapsHref).toBeNull();
  });

  describe("specs", () => {
    it("includes size, clear height, and loading docks when all present", () => {
      const specs = propertyToModel(baseProperty).specs;
      const labels = specs.map((s) => s.label);
      expect(labels).toContain("Size");
      expect(labels).toContain("Clear height");
      expect(labels).toContain("Loading docks");
    });

    it("omits size when size_sqft is null", () => {
      const specs = propertyToModel({ ...baseProperty, size_sqft: null }).specs;
      expect(specs.find((s) => s.label === "Size")).toBeUndefined();
    });

    it("omits clear height when clear_height is null", () => {
      const specs = propertyToModel({ ...baseProperty, clear_height: null }).specs;
      expect(specs.find((s) => s.label === "Clear height")).toBeUndefined();
    });

    it("omits loading docks when loading_docks is null", () => {
      const specs = propertyToModel({ ...baseProperty, loading_docks: null }).specs;
      expect(specs.find((s) => s.label === "Loading docks")).toBeUndefined();
    });

    it("returns empty specs array when all numeric fields are null", () => {
      const noSpecs = { ...baseProperty, size_sqft: null, clear_height: null, loading_docks: null };
      expect(propertyToModel(noSpecs).specs).toEqual([]);
    });

    it("formats size with SF suffix", () => {
      const spec = propertyToModel(baseProperty).specs.find((s) => s.label === "Size")!;
      expect(spec.value).toBe("10,000 SF");
    });
  });

  describe("broker", () => {
    it("trims broker name, email, and phone", () => {
      const { broker } = propertyToModel(baseProperty);
      expect(broker.name).toBe("Jane Doe");
      expect(broker.email).toBe("jane@broker.com");
      expect(broker.phone).toBe("555-0100");
    });

    it("returns null for missing broker fields", () => {
      const p = { ...baseProperty, listing_broker_name: undefined, listing_broker_email: undefined, listing_broker_phone: undefined };
      const { broker } = propertyToModel(p);
      expect(broker.name).toBeNull();
      expect(broker.email).toBeNull();
      expect(broker.phone).toBeNull();
    });
  });
});

// ---------------------------------------------------------------------------
// toPropertyModels
// ---------------------------------------------------------------------------

describe("toPropertyModels", () => {
  it("maps an array of matches preserving order", () => {
    const matches = [makeMatch({ id: "a" }), makeMatch({ id: "b" }), makeMatch({ id: "c" })];
    const models = toPropertyModels(matches);
    expect(models.map((m) => m.id)).toEqual(["a", "b", "c"]);
  });

  it("returns an empty array for empty input", () => {
    expect(toPropertyModels([])).toEqual([]);
  });

  it("passes the array index for fallback id generation", () => {
    const matches = [makeMatch({ id: null }), makeMatch({ id: null })];
    const models = toPropertyModels(matches);
    expect(models[0].id).toBe("match-0");
    expect(models[1].id).toBe("match-1");
  });
});

// ---------------------------------------------------------------------------
// detailToModel
// ---------------------------------------------------------------------------

describe("detailToModel", () => {
  const detail: ListingDetailResponse = {
    property: baseProperty,
    images: ["https://example.com/a.jpg", "https://example.com/b.jpg"],
  };

  it("uses detail.images as galleryImgs when non-empty", () => {
    expect(detailToModel(detail).galleryImgs).toEqual([
      "https://example.com/a.jpg",
      "https://example.com/b.jpg",
    ]);
  });

  it("falls back to property image when detail.images is empty", () => {
    const noImages = { ...detail, images: [] };
    expect(detailToModel(noImages).galleryImgs).toEqual(["https://example.com/img.jpg"]);
  });

  it("preserves all other PropertyModel fields", () => {
    const model = detailToModel(detail);
    expect(model.href).toBe("/listings/p-1");
    expect(model.broker.name).toBe("Jane Doe");
    expect(model.specs.length).toBeGreaterThan(0);
  });
});
