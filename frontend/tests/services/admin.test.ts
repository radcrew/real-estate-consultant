import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { AdminService } from "@services/admin";

const makeHttp = (data: unknown = {}) =>
  ({ post: vi.fn().mockResolvedValue({ data }) }) as unknown as AxiosInstance;

const jobResponse = {
  job_id: "job-1",
  source: "loopnet-seed",
  status: "queued",
  idempotency_key: "key-1",
};

describe("AdminService", () => {
  describe("enqueueIngest", () => {
    it("calls POST /admin/ingest with the given source", async () => {
      const http = makeHttp(jobResponse);
      const data = await new AdminService(http).enqueueIngest("loopnet-seed");
      expect(http.post).toHaveBeenCalledWith(
        "/admin/ingest",
        { source: "loopnet-seed" },
        expect.any(Object),
      );
      expect(data).toEqual(jobResponse);
    });

    it("defaults source to 'loopnet-seed' when not provided", async () => {
      const http = makeHttp(jobResponse);
      await new AdminService(http).enqueueIngest();
      expect(http.post).toHaveBeenCalledWith(
        "/admin/ingest",
        { source: "loopnet-seed" },
        expect.any(Object),
      );
    });
  });
});
