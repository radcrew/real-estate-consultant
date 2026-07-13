"use client";

import { NoticeCard } from "@components/ui/notice-card";
import { Badge, type BadgeColor } from "@components/ui/badge";
import { ButtonPrimary } from "@components/ui/button-primary";
import { useIngestJob, type JobStatus } from "@hooks/use-ingest-job";

const STATUS_COLOR: Record<JobStatus, BadgeColor> = {
  pending: "yellow",
  running: "blue",
  done: "green",
  failed: "red",
};

export const AdminIngestView = () => {
  const { job, error, triggering, isBusy, triggerIngest } = useIngestJob();

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
