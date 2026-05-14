import type { AxiosInstance } from "axios";
import { isAxiosError } from "axios";

import { apiClient } from "@lib/api-client";

export type OutreachDraft = {
  id: string;
  property_id: string | null;
  user_id: string | null;
  draft_email: string | null;
  created_at: string | null;
};

export class OutreachService {
  constructor(private readonly http: AxiosInstance) {}

  async getLatestDraft(
    propertyId: string,
    options?: { signal?: AbortSignal },
  ): Promise<OutreachDraft | null> {
    try {
      const { data } = await this.http.get<OutreachDraft>("/outreach/drafts/latest", {
        params: { property_id: propertyId },
        signal: options?.signal,
      });
      return data;
    } catch (err: unknown) {
      if (isAxiosError(err) && err.response?.status === 404) {
        return null;
      }
      throw err;
    }
  }

  async createDraft(
    propertyId: string,
    options?: { signal?: AbortSignal },
  ): Promise<OutreachDraft> {
    const { data } = await this.http.post<OutreachDraft>(
      "/outreach/drafts",
      { property_id: propertyId },
      { signal: options?.signal },
    );
    return data;
  }

  async patchDraft(
    draftId: string,
    body: { draft_email: string },
    options?: { signal?: AbortSignal },
  ): Promise<OutreachDraft> {
    const { data } = await this.http.patch<OutreachDraft>(`/outreach/drafts/${draftId}`, body, {
      signal: options?.signal,
    });
    return data;
  }
}

export const outreachService = new OutreachService(apiClient);
