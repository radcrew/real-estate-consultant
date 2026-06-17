import axios from "axios";
import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { OutreachService } from "@services/outreach";
import type { OutreachDraft } from "@services/outreach";

const draft: OutreachDraft = {
  id: "d-1",
  property_id: "p-1",
  user_id: "u-1",
  draft_email: "Hi there,\n\nI am interested.",
  created_at: "2024-01-01T00:00:00Z",
};

const makeHttp = (data: unknown = {}) =>
  ({
    get: vi.fn().mockResolvedValue({ data }),
    post: vi.fn().mockResolvedValue({ data }),
    patch: vi.fn().mockResolvedValue({ data }),
  }) as unknown as AxiosInstance;

const makeFailingGet = (status: number) => {
  const err = new axios.AxiosError("error");
  err.response = { status, data: {}, headers: {}, config: {} as never, statusText: "" };
  return {
    get: vi.fn().mockRejectedValue(err),
    post: vi.fn(),
    patch: vi.fn(),
  } as unknown as AxiosInstance;
};

describe("OutreachService", () => {
  describe("getLatestDraft", () => {
    it("calls GET /outreach/drafts/latest with property_id param", async () => {
      const http = makeHttp(draft);
      await new OutreachService(http).getLatestDraft("p-1");
      expect(http.get).toHaveBeenCalledWith(
        "/outreach/drafts/latest",
        expect.objectContaining({ params: { property_id: "p-1" } }),
      );
    });

    it("returns the draft on success", async () => {
      const http = makeHttp(draft);
      expect(await new OutreachService(http).getLatestDraft("p-1")).toEqual(draft);
    });

    it("returns null on a 404 response", async () => {
      const http = makeFailingGet(404);
      expect(await new OutreachService(http).getLatestDraft("p-1")).toBeNull();
    });

    it("re-throws non-404 errors", async () => {
      const http = makeFailingGet(500);
      await expect(new OutreachService(http).getLatestDraft("p-1")).rejects.toThrow();
    });
  });

  describe("createDraft", () => {
    it("calls POST /outreach/drafts with property_id and returns data", async () => {
      const http = makeHttp(draft);
      const data = await new OutreachService(http).createDraft("p-1");
      expect(http.post).toHaveBeenCalledWith(
        "/outreach/drafts",
        { property_id: "p-1" },
        expect.any(Object),
      );
      expect(data).toEqual(draft);
    });
  });

  describe("patchDraft", () => {
    it("calls PATCH /outreach/drafts/{id} with body and returns data", async () => {
      const http = makeHttp(draft);
      const body = { draft_email: "Updated email" };
      const data = await new OutreachService(http).patchDraft("d-1", body);
      expect(http.patch).toHaveBeenCalledWith("/outreach/drafts/d-1", body, expect.any(Object));
      expect(data).toEqual(draft);
    });
  });
});
