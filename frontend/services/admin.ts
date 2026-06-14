import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type EnqueueIngestResponse = {
  job_id: string;
  source: string;
  status: string;
  idempotency_key: string;
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
}

export const adminService = new AdminService(apiClient);
