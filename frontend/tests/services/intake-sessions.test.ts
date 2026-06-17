import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { IntakeSessionsService } from "@services/intake-sessions";

const makeHttp = (data: unknown = {}) =>
  ({
    get: vi.fn().mockResolvedValue({ data }),
    post: vi.fn().mockResolvedValue({ data }),
    patch: vi.fn().mockResolvedValue({ data }),
  }) as unknown as AxiosInstance;

describe("IntakeSessionsService", () => {
  describe("createSession", () => {
    it("calls POST /intake-sessions with mode=guided param", async () => {
      const http = makeHttp({ mode: "guided", session_id: "s-1", status: "active", current_index: 0 });
      await new IntakeSessionsService(http).createSession("guided");
      expect(http.post).toHaveBeenCalledWith(
        "/intake-sessions",
        undefined,
        expect.objectContaining({ params: { mode: "guided" } }),
      );
    });

    it("calls POST /intake-sessions with mode=llm param", async () => {
      const http = makeHttp({ mode: "llm", session_id: "s-2", status: "active", current_index: 0, total_questions: 5, message: "Hi", next_question: null });
      await new IntakeSessionsService(http).createSession("llm");
      expect(http.post).toHaveBeenCalledWith(
        "/intake-sessions",
        undefined,
        expect.objectContaining({ params: { mode: "llm" } }),
      );
    });

    it("returns the data from the response", async () => {
      const payload = { mode: "guided" as const, session_id: "s-1", status: "active", current_index: 0 };
      const http = makeHttp(payload);
      const data = await new IntakeSessionsService(http).createSession("guided");
      expect(data).toEqual(payload);
    });
  });

  describe("getSession", () => {
    it("calls GET /intake-sessions/{id} and returns data", async () => {
      const http = makeHttp({ id: "s-1", status: "active" });
      const data = await new IntakeSessionsService(http).getSession("s-1");
      expect(http.get).toHaveBeenCalledWith("/intake-sessions/s-1");
      expect(data).toEqual({ id: "s-1", status: "active" });
    });
  });

  describe("submitAnswer", () => {
    it("calls PATCH /intake-sessions/{id}/answers/guided with body", async () => {
      const http = makeHttp({ session: {}, next_question: null });
      const body = { key: "location", answers: "Austin, TX" };
      await new IntakeSessionsService(http).submitAnswer("s-1", body);
      expect(http.patch).toHaveBeenCalledWith("/intake-sessions/s-1/answers/guided", body);
    });
  });

  describe("completeSession", () => {
    it("calls POST /intake-sessions/{id}/complete and returns data", async () => {
      const http = makeHttp({ id: "s-1", status: "completed", search_profile_id: "sp-1" });
      const data = await new IntakeSessionsService(http).completeSession("s-1");
      expect(http.post).toHaveBeenCalledWith("/intake-sessions/s-1/complete");
      expect(data).toEqual({ id: "s-1", status: "completed", search_profile_id: "sp-1" });
    });
  });

  describe("submitLlmInput", () => {
    it("calls POST /intake-sessions/{id}/answers/llm with body", async () => {
      const http = makeHttp({ mode: "llm", is_complete: false });
      const body = { input: "warehouse in Austin", mode: "llm" as const };
      await new IntakeSessionsService(http).submitLlmInput("s-1", body);
      expect(http.post).toHaveBeenCalledWith("/intake-sessions/s-1/answers/llm", body);
    });
  });
});
