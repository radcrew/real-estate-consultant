"use client";

import { useCallback, useEffect, useState } from "react";

import { adminService, type JobRow } from "@services/admin";
import { getApiErrorMessage } from "@utils/common";

export type { JobResult, JobRow, JobStatus } from "@services/admin";

// How often to re-read a pending or running job. Ingestion runs take minutes.
export const JOB_POLL_INTERVAL_MS = 2000;

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

  const isBusy = job?.status === "pending" || job?.status === "running";

  // Poll through the backend while the job is active. Each status change schedules the
  // next read; reaching done/failed stops it.
  useEffect(() => {
    if (!job || !isBusy) return;

    let cancelled = false;
    const timer = setTimeout(() => {
      adminService
        .getJob(job.id)
        .then((next) => {
          if (!cancelled) setJob(next);
        })
        .catch((e) => {
          if (!cancelled) setError(getApiErrorMessage(e));
        });
    }, JOB_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [job, isBusy]);

  const triggerIngest = useCallback(async () => {
    setError(null);
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
