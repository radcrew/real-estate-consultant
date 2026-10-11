import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type EnqueueIngestResponse = {
  job_id: string;
  source: string;
  status: string;
  idempotency_key: string;
};

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

export class AdminService {
  constructor(private readonly http: AxiosInstance) {}

  async enqueueIngest(
    source = "loopnet-seed",
    options?: { signal?: AbortSignal },
  ): Promise<EnqueueIngestResponse> {
    const { data } = await this.http.post<EnqueueIngestResponse>(
      "/admin/ingest",
      { source },
      { signal: options?.signal },
    );
    return data;
  }

  async getJob(jobId: string): Promise<JobRow> {
    const { data } = await this.http.get<JobRow>(`/admin/jobs/${encodeURIComponent(jobId)}`);
    return data;
  }
}

export const adminService = new AdminService(apiClient);
