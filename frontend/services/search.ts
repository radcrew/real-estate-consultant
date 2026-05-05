import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

/**
 * One property row from search ``results[].property`` (snake_case JSON from the API).
 */
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

/**
 * One ranked row: property payload plus match score (0–100).
 */
export type SearchPropertyMatch = {
  property: SearchProperty;
  match_score: number;
};

/**
 * Response body from ``GET /api/v1/search/{session_profile_id}?limit=&offset=``.
 * ``criteria`` keys are criterion objects shaped like ``{ type, data }`` (see ``@lib/search-criteria``).
 */
export type SearchResponse = {
  criteria: Record<string, unknown>;
  results: SearchPropertyMatch[];
  total: number;
  limit: number;
  offset: number;
};

export class SearchService {
  constructor(private readonly http: AxiosInstance) {}

  async search(
    sessionProfileId: string,
    pagination?: { limit?: number; offset?: number },
  ): Promise<SearchResponse> {
    const { data } = await this.http.get<SearchResponse>(`/search/${sessionProfileId}`, {
      params: pagination,
    });
    return data;
  }
}

export const searchService = new SearchService(apiClient);
