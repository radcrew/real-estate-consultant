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
  listing_broker_name?: string | null;
  listing_broker_email?: string | null;
  listing_broker_phone?: string | null;
  image?: string | null;
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

export type QuickSearchBody = {
  location?: string;
  property_types?: string[];
  price_min?: number;
  price_max?: number;
};

export type QuickSearchResponse = {
  search_profile_id: string;
};

export type UpdateSearchCriteriaBody = Record<string, unknown>;

export type SearchFiltersResponse = Record<string, unknown>;

export type FitScoreBreakdown = {
  location: number;
  price: number;
  size: number;
  total: number;
};

export type FitExplanation = {
  property_id: string;
  score: FitScoreBreakdown;
  summary: string;
  strengths: string[];
  considerations: string[];
};

export class SearchService {
  constructor(private readonly http: AxiosInstance) {}

  async quickSearch(body: QuickSearchBody): Promise<QuickSearchResponse> {
    const { data } = await this.http.post<QuickSearchResponse>("/search/quick", body);
    return data;
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

  async explainFit(
    sessionProfileId: string,
    propertyId: string,
    options?: { signal?: AbortSignal },
  ): Promise<FitExplanation> {
    const { data } = await this.http.post<FitExplanation>(
      `/search/${sessionProfileId}/fit/${propertyId}`,
      undefined,
      { signal: options?.signal },
    );
    return data;
  }
}

export const searchService = new SearchService(apiClient);
