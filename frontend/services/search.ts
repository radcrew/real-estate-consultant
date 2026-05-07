import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type SearchProperty = {
  id: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  latitude: number | null;
  longitude: number | null;
  property_type: string | null;
  listing_type: string | null;
  description: string | null;
  size_sqft: number | null;
  price: number | null;
  rent: number | null;
  clear_height: number | null;
  loading_docks: number | null;
};

export type SearchPropertyMatch = {
  property: SearchProperty;
  match_score: number;
};

export type SearchResponse = {
  criteria: Record<string, unknown>;
  results: SearchPropertyMatch[];
  total: number;
  limit: number;
  offset: number;
};

export type UpdateSearchCriteriaBody = Record<string, unknown>;

export type SearchFiltersResponse = Record<string, unknown>;

export class SearchService {
  constructor(private readonly http: AxiosInstance) {}

  async getFilters(options?: { signal?: AbortSignal }): Promise<SearchFiltersResponse> {
    const { data } = await this.http.get<SearchFiltersResponse>("/filters", {
      signal: options?.signal,
    });
    if (data !== null) {
      return data;
    }
    return {};
  }

  async search(
    sessionProfileId: string,
    pagination?: { limit?: number; offset?: number },
  ): Promise<SearchResponse> {
    const { data } = await this.http.get<SearchResponse>(`/search/${sessionProfileId}`, {
      params: pagination,
    });
    return data;
  }

  async updateCriteria(
    sessionProfileId: string,
    criteria: UpdateSearchCriteriaBody,
  ): Promise<void> {
    await this.http.put(`/search/${sessionProfileId}`, criteria);
  }
}

export const searchService = new SearchService(apiClient);
