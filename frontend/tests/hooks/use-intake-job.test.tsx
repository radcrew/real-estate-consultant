// @vitest-environment jsdom
import { StrictMode } from "react";
import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockEnqueue = vi.fn();
const mockGetJob = vi.fn();

vi.mock("@services/intake-sessions", () => ({
  TERMINAL_JOB_STATUSES: ["succeeded", "failed"],
  intakeSessionsService: {
    enqueueLlmInput: (...a: unknown[]) => mockEnqueue(...a),
    getLlmJob: (...a: unknown[]) => mockGetJob(...a),
  },
}));

const { useIntakeJob } = await import("@hooks/use-intake-job");

const RESULT = { criteria: { location: "Austin" }, missing_fields: [] };

const queued = { job_id: "job-1", status: "queued" };
const succeeded = { job_id: "job-1", status: "succeeded", result: RESULT, error: null };

beforeEach(() => {
  vi.clearAllMocks();
});

describe("useIntakeJob", () => {
  it("polls until the turn settles", async () => {
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob
      .mockResolvedValueOnce({ job_id: "job-1", status: "running", result: null, error: null })
      .mockResolvedValue(succeeded);

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).toHaveBeenCalledTimes(2);
  }, 10_000);

  it("skips polling when the turn already ran inline", async () => {
    // No queue configured: the 202 comes back terminal, so there is nothing to wait for.
    mockEnqueue.mockResolvedValue({ job_id: "job-1", status: "succeeded" });
    mockGetJob.mockResolvedValue(succeeded);

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).toHaveBeenCalledTimes(1);
  });

  it("keeps polling through a failed request", async () => {
    // One bad response is not a dead turn; the server is very likely still working.
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockRejectedValueOnce(new Error("network blip")).mockResolvedValue(succeeded);

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
    expect(mockGetJob).toHaveBeenCalledTimes(2);
  }, 10_000);

  it("gives up after repeated failures instead of retrying to the deadline", async () => {
    // A fault that repeats is not a blip. Retrying it for ten minutes makes a broken
    // turn look identical to a slow one, and the user never sees an error at all.
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockRejectedValue(new Error("upstream on fire"));

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow(
      "upstream on fire",
    );
    expect(mockGetJob).toHaveBeenCalledTimes(3);
  }, 10_000);

  it.each([401, 403, 422])("stops immediately on a %s", async (status) => {
    // Client errors are answers, not blips — retrying only delays telling the user.
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockRejectedValue(
      Object.assign(new Error("client error"), {
        isAxiosError: true,
        response: { status },
      }),
    );

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow();
    expect(mockGetJob).toHaveBeenCalledTimes(1);
  });

  it("keeps waiting through a 429, which does clear on its own", async () => {
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob
      .mockRejectedValueOnce(
        Object.assign(new Error("rate limited"), {
          isAxiosError: true,
          response: { status: 429 },
        }),
      )
      .mockResolvedValue(succeeded);

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
  }, 10_000);

  it("stops immediately when the job does not exist", async () => {
    // The one answer retrying cannot improve.
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockRejectedValue(
      Object.assign(new Error("not found"), {
        isAxiosError: true,
        response: { status: 404 },
      }),
    );

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow();
    expect(mockGetJob).toHaveBeenCalledTimes(1);
  });

  it("rejects with the reason the backend recorded", async () => {
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockResolvedValue({
      job_id: "job-1",
      status: "failed",
      result: null,
      error: "The assistant's reply didn't come through.",
    });

    const { result } = renderHook(() => useIntakeJob());
    await expect(result.current.runTurn("sess-1", "warehouse")).rejects.toThrow(
      "The assistant's reply didn't come through.",
    );
  });

  it("still works under StrictMode's double mount", async () => {
    // Next enables StrictMode in development, which mounts, unmounts and remounts. A
    // flag only set to true on cleanup stays true through that, so every turn aborted on
    // its first poll — in development only, which is where the app is actually used.
    mockEnqueue.mockResolvedValue(queued);
    mockGetJob.mockResolvedValue(succeeded);

    const { result } = renderHook(() => useIntakeJob(), { wrapper: StrictMode });
    await expect(result.current.runTurn("sess-1", "warehouse")).resolves.toEqual(RESULT);
  });

  it("stops polling when the component unmounts", async () => {
    // Nothing else can cancel the loop, so without its own check it would keep calling
    // the API for the full deadline after the user closed the wizard.
    mockEnqueue.mockResolvedValue(queued);
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
});
