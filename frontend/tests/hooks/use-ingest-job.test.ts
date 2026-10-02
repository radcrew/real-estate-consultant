// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@services/admin", () => ({
  adminService: { enqueueIngest: vi.fn(), getJob: vi.fn() },
}));

import { adminService, type JobRow } from "@services/admin";
import { JOB_POLL_INTERVAL_MS, useIngestJob } from "@hooks/use-ingest-job";

const enqueueIngest = vi.mocked(adminService.enqueueIngest);
const getJob = vi.mocked(adminService.getJob);

const job = (status: JobRow["status"]): JobRow => ({
  id: "job-1",
  source: "loopnet-seed",
  status,
  attempts: 1,
  result: status === "done" ? { fetched: 10, normalized: 9, rejected: 1 } : null,
  error: null,
});

beforeEach(() => {
  vi.useFakeTimers();
  enqueueIngest.mockResolvedValue({
    job_id: "job-1",
    source: "loopnet-seed",
    status: "pending",
    idempotency_key: "k",
  });
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

const advancePoll = () =>
  act(async () => {
    await vi.advanceTimersByTimeAsync(JOB_POLL_INTERVAL_MS);
  });

describe("useIngestJob", () => {
  it("enqueues, loads the job and polls until it finishes", async () => {
    getJob
      .mockResolvedValueOnce(job("pending"))
      .mockResolvedValueOnce(job("running"))
      .mockResolvedValueOnce(job("done"));
    const { result } = renderHook(() => useIngestJob());

    await act(() => result.current.triggerIngest());
    expect(result.current.job?.status).toBe("pending");
    expect(result.current.isBusy).toBe(true);

    await advancePoll();
    expect(result.current.job?.status).toBe("running");

    await advancePoll();
    expect(result.current.job?.status).toBe("done");
    expect(result.current.isBusy).toBe(false);

    // Finished: no further reads.
    await advancePoll();
    expect(getJob).toHaveBeenCalledTimes(3);
  });

  it("surfaces an enqueue error", async () => {
    enqueueIngest.mockRejectedValue(new Error("boom"));
    const { result } = renderHook(() => useIngestJob());

    await act(() => result.current.triggerIngest());

    expect(result.current.error).toBeTruthy();
    expect(result.current.job).toBeNull();
    expect(result.current.triggering).toBe(false);
  });

  it("surfaces a polling error and stops polling", async () => {
    getJob.mockResolvedValueOnce(job("running")).mockRejectedValueOnce(new Error("down"));
    const { result } = renderHook(() => useIngestJob());

    await act(() => result.current.triggerIngest());
    await advancePoll();

    expect(result.current.error).toBeTruthy();
    await advancePoll();
    expect(getJob).toHaveBeenCalledTimes(2);
  });

  it("stops polling on unmount", async () => {
    getJob.mockResolvedValue(job("running"));
    const { result, unmount } = renderHook(() => useIngestJob());

    await act(() => result.current.triggerIngest());
    unmount();
    await vi.advanceTimersByTimeAsync(JOB_POLL_INTERVAL_MS * 3);

    expect(getJob).toHaveBeenCalledTimes(1);
  });
});
