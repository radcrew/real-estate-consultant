import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";
import type { SearchProperty } from "@services/search";

export type ListingProperty = SearchProperty;

export type ListingDetailResponse = {
  property: ListingProperty;
  images: string[];
};

export type ListingSubmissionPayload = {
  property_type: string;
  listing_type: string;
  title: string;
  description?: string | null;
  address?: string | null;
  city: string;
  state: string;
  size_sqft?: number | null;
  price?: number | null;
  clear_height?: number | null;
  loading_docks?: number | null;
  contact_name: string;
  contact_email: string;
};

export type ListingSubmissionResult = { id: string; status: string };

export type AgentProfileResponse = {
  name: string;
  email?: string | null;
  phone?: string | null;
  properties: ListingProperty[];
};

export class ListingsService {
  constructor(private readonly http: AxiosInstance) {}

  async getListing(
    propertyId: string,
    options?: { signal?: AbortSignal },
  ): Promise<ListingDetailResponse> {
    const { data } = await this.http.get<ListingDetailResponse>(`/listings/${propertyId}`, {
      signal: options?.signal,
    });
    return data;
  }

  async submitListing(
    payload: ListingSubmissionPayload,
    options?: { signal?: AbortSignal },
  ): Promise<ListingSubmissionResult> {
    const { data } = await this.http.post<ListingSubmissionResult>(
      "/listing-submissions",
      payload,
      { signal: options?.signal },
    );
    return data;
  }

  async getAgent(
    broker: string,
    options?: { signal?: AbortSignal },
  ): Promise<AgentProfileResponse> {
    const { data } = await this.http.get<AgentProfileResponse>(
      `/agents/${encodeURIComponent(broker)}`,
      { signal: options?.signal },
    );
    return data;
  }
}

export const listingsService = new ListingsService(apiClient);
