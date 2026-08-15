// @vitest-environment jsdom
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockEnqueue = vi.fn();
const mockGetJob = vi.fn();
const mockSubscribe = vi.fn();

vi.mock("@services/intake-sessions", () => ({
  TERMINAL_JOB_STATUSES: ["succeeded", "failed"],
  intakeSessionsService: {
    enqueueLlmInput: (...a: unknown[]) => mockEnqueue(...a),
    getLlmJob: (...a: unknown[]) => mockGetJob(...a),
  },
  subscribeToJob: (...a: unknown[]) => mockSubscribe(...a),
}));

const { useIntakeJob } = await import("@hooks/use-intake-job");

const RESULT = { criteria: { location: "Austin" }, missing_fields: [] };

beforeEach(() => {
  vi.clearAllMocks();
  mockSubscribe.mockReturnValue(() => {});
});

describe("useIntakeJob", () => {
  it("resolves with the result once the job settles over the stream", async () => {
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onSettled({ job_id: "job-1", status: "succeeded", result: RESULT, error: null });
      return () => {};
    });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).not.toHaveBeenCalled();
  });

  it("skips the stream when the turn already ran inline", async () => {
    // No queue configured: the 202 comes back already terminal, so opening a stream
    // would only add a round trip.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "succeeded" });
    mockGetJob.mockResolvedValue({
      job_id: "job-1", status: "succeeded", result: RESULT, error: null,
    });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockSubscribe).not.toHaveBeenCalled();
  });

  it("falls back to polling when the stream drops", async () => {
    // A dropped EventSource with nothing behind it would strand a turn the backend has
    // already paid a model to run.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onStreamLost();
      return () => {};
    });
    mockGetJob.mockResolvedValue({
      job_id: "job-1", status: "succeeded", result: RESULT, error: null,
    });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).toHaveBeenCalled();
  });

  it("keeps polling through a failed request", async () => {
    // Polling runs because the stream already broke, so the connection is known bad —
    // one failed response must not discard a turn the server is still processing.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onStreamLost();
      return () => {};
    });
    mockGetJob
      .mockRejectedValueOnce(new Error("network blip"))
      .mockResolvedValue({ job_id: "job-1", status: "succeeded", result: RESULT, error: null });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).toHaveBeenCalledTimes(2);
  }, 10_000);

  it("stops immediately when the job does not exist", async () => {
    // The one answer retrying cannot improve.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onStreamLost();
      return () => {};
    });
    const notFound = Object.assign(new Error("not found"), {
      isAxiosError: true,
      response: { status: 404 },
    });
    mockGetJob.mockRejectedValue(notFound);

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow();
    expect(mockGetJob).toHaveBeenCalledTimes(1);
  });

  it("rejects with the reason the backend recorded", async () => {
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onSettled({
        job_id: "job-1",
        status: "failed",
        result: null,
        error: "The assistant's reply didn't come through.",
      });
      return () => {};
    });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow(
      "The assistant's reply didn't come through.",
    );
  });

  it("stops polling when the component unmounts", async () => {
    // Closing the stream on unmount is not enough: once polling has taken over there is
    // no EventSource left to close, so without its own check the loop keeps calling the
    // API for the full deadline after the user has closed the wizard.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation((_s, _j, handlers) => {
      handlers.onStreamLost();
      return () => {};
    });
    mockGetJob.mockResolvedValue({
      job_id: "job-1", status: "running", result: null, error: null,
    });

    const { result, unmount } = renderHook(() => useIntakeJob());
    const pending = result.current.runTurn("sess-1", "warehouse").catch(() => "stopped");
    await waitFor(() => expect(mockGetJob).toHaveBeenCalled());

    unmount();
    await expect(pending).resolves.toBe("stopped");

    const afterUnmount = mockGetJob.mock.calls.length;
    await new Promise((r) => setTimeout(r, 1_500));
    expect(mockGetJob.mock.calls.length).toBe(afterUnmount);
  }, 10_000);

  it("closes the stream when the component unmounts mid-turn", async () => {
    const close = vi.fn();
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "queued" });
    mockSubscribe.mockImplementation(() => close);

    const { result, unmount } = renderHook(() => useIntakeJob());
    void result.current.runTurn("sess-1", "warehouse");
    await waitFor(() => expect(mockSubscribe).toHaveBeenCalled());
    unmount();
    expect(close).toHaveBeenCalled();
  });
});
