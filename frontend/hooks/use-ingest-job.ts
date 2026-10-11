"use client";

import { useCallback, useEffect, useState } from "react";

import { adminService, type JobRow } from "@services/admin";
import { getApiErrorMessage } from "@utils/common";

export type { JobResult, JobRow, JobStatus } from "@services/admin";

// How often to re-read a pending or running job. Ingestion runs take minutes.
export const JOB_POLL_INTERVAL_MS = 2000;
// Failed reads in a row before polling gives up and leaves the error on screen.
export const JOB_POLL_MAX_FAILURES = 5;

type UseIngestJobResult = {
  job: JobRow | null;
  error: string | null;
  triggering: boolean;
  isBusy: boolean;
  triggerIngest: () => Promise<void>;
};

export const useIngestJob = (): UseIngestJobResult => {
  const [job, setJob] = useState<JobRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [failures, setFailures] = useState(0);

  const isBusy = job?.status === "pending" || job?.status === "running";

  // Poll through the backend while the job is active. Each read, ok or failed, schedules
  // the next one; reaching done/failed or too many failures in a row stops it.
  useEffect(() => {
    if (!job || !isBusy || failures >= JOB_POLL_MAX_FAILURES) return;

    let cancelled = false;
    const timer = setTimeout(() => {
      adminService
        .getJob(job.id)
        .then((next) => {
          if (cancelled) return;
          setJob(next);
          setFailures(0);
          setError(null);
        })
        .catch((e) => {
          if (cancelled) return;
          setError(getApiErrorMessage(e));
          setFailures((n) => n + 1);
        });
    }, JOB_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [job, isBusy, failures]);

  const triggerIngest = useCallback(async () => {
    setError(null);
    setFailures(0);
    setTriggering(true);
    try {
      const enqueued = await adminService.enqueueIngest();
      setJob(await adminService.getJob(enqueued.job_id));
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setTriggering(false);
    }
  }, []);

  return { job, error, triggering, isBusy, triggerIngest };
};
