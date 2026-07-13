"use client";

import { useCallback, useEffect, useState } from "react";
import { isAxiosError } from "axios";

import { adminService } from "@services/admin";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";
import { getApiErrorMessage } from "@utils/common";

export type JobStatus = "pending" | "running" | "done" | "failed";

export type JobResult = {
  fetched?: number;
  normalized?: number;
  rejected?: number;
} | null;

export type JobRow = {
  id: string;
  source: string;
  status: JobStatus;
  attempts: number;
  result: JobResult;
  error: string | null;
};

const JOB_COLUMNS = "id, source, status, attempts, result, error";

// Supabase query errors aren't AxiosErrors, so getApiErrorMessage falls back
// to a generic message for them — surface their .message instead.
const describeError = (e: unknown): string => {
  if (isAxiosError(e)) return getApiErrorMessage(e);
  if (e instanceof Error) return e.message;
  return "Request failed.";
};

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

  useEffect(() => {
    if (!job) return;

    const supabase = getSupabaseBrowserClient();
    const channel = supabase
      .channel(`jobs-${job.id}`)
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "jobs", filter: `id=eq.${job.id}` },
        (payload) => setJob(payload.new as JobRow),
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
    // Re-subscribe only when the job id changes, not on every realtime update.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job?.id]);

  const triggerIngest = useCallback(async () => {
    setError(null);
    setTriggering(true);
    try {
      const enqueued = await adminService.enqueueIngest();
      const supabase = getSupabaseBrowserClient();
      const { data, error: fetchError } = await supabase
        .from("jobs")
        .select(JOB_COLUMNS)
        .eq("id", enqueued.job_id)
        .single();
      if (fetchError) throw fetchError;
      setJob(data as JobRow);
    } catch (e) {
      setError(describeError(e));
    } finally {
      setTriggering(false);
    }
  }, []);

  const isBusy = job?.status === "pending" || job?.status === "running";

  return { job, error, triggering, isBusy, triggerIngest };
};
