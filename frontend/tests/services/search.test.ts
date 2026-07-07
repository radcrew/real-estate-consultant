import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { SearchService } from "@services/search";
import type { SearchResponse } from "@services/search";

const makeHttp = (data: unknown = {}) =>
  ({
    get: vi.fn().mockResolvedValue({ data }),
    post: vi.fn().mockResolvedValue({ data }),
    put: vi.fn().mockResolvedValue({ data }),
  }) as unknown as AxiosInstance;

const searchResponse: SearchResponse = {
  criteria: {},
  results: [],
  total: 0,
  limit: 10,
  offset: 0,
};

describe("SearchService", () => {
  describe("quickSearch", () => {
    it("calls POST /search/quick with body and returns data", async () => {
      const http = makeHttp({ search_profile_id: "sp-1" });
      const body = { location: "Austin, TX", property_types: ["Warehouse"] };
      const data = await new SearchService(http).quickSearch(body);
      expect(http.post).toHaveBeenCalledWith("/search/quick", body);
      expect(data).toEqual({ search_profile_id: "sp-1" });
    });
  });

  describe("search", () => {
    it("calls GET /search/{profileId} and returns data", async () => {
      const http = makeHttp(searchResponse);
      const data = await new SearchService(http).search("sp-1");
      expect(http.get).toHaveBeenCalledWith("/search/sp-1", expect.any(Object));
      expect(data).toEqual(searchResponse);
    });

    it("passes pagination params", async () => {
      const http = makeHttp(searchResponse);
      await new SearchService(http).search("sp-1", { limit: 5, offset: 10 });
      expect(http.get).toHaveBeenCalledWith(
        "/search/sp-1",
        expect.objectContaining({ params: { limit: 5, offset: 10 } }),
      );
    });
  });

  describe("updateCriteria", () => {
    it("calls PUT /search/{profileId} with criteria", async () => {
      const http = makeHttp();
      const criteria = { price: { min: 100_000 } };
      await new SearchService(http).updateCriteria("sp-1", criteria);
      expect(http.put).toHaveBeenCalledWith("/search/sp-1", criteria);
    });
  });

  describe("explainFit", () => {
    it("calls POST /search/{profileId}/fit/{propertyId} and returns data", async () => {
      const explanation = {
        property_id: "prop-1",
        score: { location: 1, price: 0.8, size: 0.6, total: 82 },
        summary: "Good match.",
        strengths: ["Right city"],
        considerations: [],
      };
      const http = makeHttp(explanation);
      const data = await new SearchService(http).explainFit("sp-1", "prop-1");
      expect(http.post).toHaveBeenCalledWith(
        "/search/sp-1/fit/prop-1",
        undefined,
        expect.any(Object),
      );
      expect(data).toEqual(explanation);
    });
  });
});
