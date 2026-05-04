import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

/** Response from ``GET /api/v1/search/{search_profile_id}``. */
export type SearchByProfileResponse = {
  criteria: Record<string, unknown>;
};

export class SearchService {
  constructor(private readonly http: AxiosInstance) {}

  async search(searchProfileId: string): Promise<SearchByProfileResponse> {
    const { data } = await this.http.get<SearchByProfileResponse>(`/search/${searchProfileId}`);
    return data;
  }
}

export const searchService = new SearchService(apiClient);
