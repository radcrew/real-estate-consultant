import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { ListingsService } from "@services/listings";
import type { ListingDetailResponse, ListingSubmissionPayload } from "@services/listings";

const makeHttp = (data: unknown = {}) =>
  ({
    get: vi.fn().mockResolvedValue({ data }),
    post: vi.fn().mockResolvedValue({ data }),
    patch: vi.fn().mockResolvedValue({ data }),
  }) as unknown as AxiosInstance;

const detailResponse: ListingDetailResponse = {
  property: {
    id: "p-1",
    address: "1 Main St",
    city: "Austin",
    state: "TX",
    country: "US",
    latitude: null,
    longitude: null,
    property_type: "Warehouse",
    listing_type: "For Sale",
    description: null,
    size_sqft: 5000,
    price: 500_000,
    rent: null,
    clear_height: null,
    loading_docks: null,
  },
  images: [],
};

const submission: ListingSubmissionPayload = {
  property_type: "Warehouse",
  listing_type: "For Sale",
  title: "Big Warehouse",
  city: "Austin",
  state: "TX",
  contact_name: "Jane Doe",
  contact_email: "jane@example.com",
};

describe("ListingsService", () => {
  describe("getFeaturedListings", () => {
    it("calls GET /listings/featured and returns data", async () => {
      const http = makeHttp({ listings: [] });
      const data = await new ListingsService(http).getFeaturedListings();
      expect(http.get).toHaveBeenCalledWith("/listings/featured", expect.any(Object));
      expect(data).toEqual({ listings: [] });
    });
  });

  describe("getListing", () => {
    it("calls GET /listings/{id} and returns data", async () => {
      const http = makeHttp(detailResponse);
      const data = await new ListingsService(http).getListing("p-1");
      expect(http.get).toHaveBeenCalledWith("/listings/p-1", expect.any(Object));
      expect(data).toEqual(detailResponse);
    });
  });

  describe("submitListing", () => {
    it("calls POST /listing-submissions with payload and returns data", async () => {
      const http = makeHttp({ id: "sub-1", status: "pending" });
      const data = await new ListingsService(http).submitListing(submission);
      expect(http.post).toHaveBeenCalledWith("/listing-submissions", submission, expect.any(Object));
      expect(data).toEqual({ id: "sub-1", status: "pending" });
    });
  });

  describe("getAgent", () => {
    it("calls GET /agents/{broker} with URL-encoded broker name", async () => {
      const http = makeHttp({ name: "Jane", properties: [] });
      await new ListingsService(http).getAgent("Jane Doe");
      expect(http.get).toHaveBeenCalledWith(
        `/agents/${encodeURIComponent("Jane Doe")}`,
        expect.any(Object),
      );
    });
  });

  describe("listSubmissions", () => {
    it("calls GET /listing-submissions and returns data", async () => {
      const http = makeHttp([]);
      const data = await new ListingsService(http).listSubmissions();
      expect(http.get).toHaveBeenCalledWith("/listing-submissions", expect.any(Object));
      expect(data).toEqual([]);
    });
  });

  describe("updateSubmission", () => {
    it("calls PATCH /listing-submissions/{id} with status", async () => {
      const http = makeHttp({ id: "sub-1", status: "approved" });
      await new ListingsService(http).updateSubmission("sub/1", "approved");
      expect(http.patch).toHaveBeenCalledWith(
        `/listing-submissions/${encodeURIComponent("sub/1")}`,
        { status: "approved" },
        expect.any(Object),
      );
    });
  });
});
