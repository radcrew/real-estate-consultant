"use client";

import { useEffect, useState } from "react";
import { isAxiosError } from "axios";

import { NoticeCard } from "@components/ui/notice-card";
import { Badge, type BadgeColor } from "@components/ui/badge";
import { ButtonPrimary } from "@components/ui/button-primary";
import { adminService } from "@services/admin";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";
import { getApiErrorMessage } from "@utils/common";

type JobStatus = "pending" | "running" | "done" | "failed";

type JobResult = {
  fetched?: number;
  normalized?: number;
  rejected?: number;
} | null;

type JobRow = {
  id: string;
  source: string;
  status: JobStatus;
  attempts: number;
  result: JobResult;
  error: string | null;
};

const STATUS_COLOR: Record<JobStatus, BadgeColor> = {
  pending: "yellow",
  running: "blue",
  done: "green",
  failed: "red",
};

const JOB_COLUMNS = "id, source, status, attempts, result, error";

// Supabase query errors aren't AxiosErrors, so getApiErrorMessage falls back
// to a generic message for them — surface their .message instead.
const describeError = (e: unknown): string => {
  if (isAxiosError(e)) return getApiErrorMessage(e);
  if (e instanceof Error) return e.message;
  return "Request failed.";
};

export const AdminIngestView = () => {
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

  const triggerIngest = async () => {
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
  };

  const isBusy = job?.status === "pending" || job?.status === "running";

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
        Ingestion
      </h1>
      <p className="mt-3 text-neutral-500 dark:text-neutral-400">
        Trigger a listing ingestion run and watch its progress live.
      </p>

      {error ? (
        <div className="mt-10 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="mt-10">
        <ButtonPrimary
          sizeClass="px-4 py-2"
          fontSize="text-sm font-medium"
          disabled={triggering || isBusy}
          onClick={() => void triggerIngest()}
        >
          {triggering ? "Starting…" : "Run ingestion"}
        </ButtonPrimary>
      </div>

      {job ? (
        <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-neutral-200 p-5 sm:flex-row sm:items-center sm:justify-between dark:border-neutral-700">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Badge name={job.status} color={STATUS_COLOR[job.status]} />
              <span className="text-xs text-neutral-500 dark:text-neutral-400">{job.source}</span>
            </div>
            {job.result ? (
              <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-300">
                Fetched {job.result.fetched ?? 0} · Normalized {job.result.normalized ?? 0} ·
                Rejected {job.result.rejected ?? 0}
              </p>
            ) : null}
            {job.error ? <p className="mt-2 text-sm text-destructive">{job.error}</p> : null}
          </div>
        </div>
      ) : (
        <NoticeCard className="mt-6 text-neutral-600 dark:text-neutral-300">
          No ingestion run started yet.
        </NoticeCard>
      )}
    </div>
  );
};
