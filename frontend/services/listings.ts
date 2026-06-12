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

export type FeaturedListingsResponse = {
  listings: ListingDetailResponse[];
};

export type AgentProfileResponse = {
  name: string;
  email?: string | null;
  phone?: string | null;
  properties: ListingProperty[];
};

export type ListingSubmissionStatus = "pending" | "approved" | "rejected";

export type ListingSubmissionItem = {
  id: string;
  status: ListingSubmissionStatus;
  property_type?: string | null;
  listing_type?: string | null;
  title?: string | null;
  city?: string | null;
  state?: string | null;
  size_sqft?: number | null;
  price?: number | null;
  contact_name?: string | null;
  contact_email?: string | null;
  created_at?: string | null;
};

export class ListingsService {
  constructor(private readonly http: AxiosInstance) {}

  async getFeaturedListings(
    options?: { signal?: AbortSignal },
  ): Promise<FeaturedListingsResponse> {
    const { data } = await this.http.get<FeaturedListingsResponse>("/listings/featured", {
      signal: options?.signal,
    });
    return data;
  }

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

  async listSubmissions(options?: { signal?: AbortSignal }): Promise<ListingSubmissionItem[]> {
    const { data } = await this.http.get<ListingSubmissionItem[]>("/listing-submissions", {
      signal: options?.signal,
    });
    return data;
  }

  async updateSubmission(
    id: string,
    status: ListingSubmissionStatus,
    options?: { signal?: AbortSignal },
  ): Promise<ListingSubmissionItem> {
    const { data } = await this.http.patch<ListingSubmissionItem>(
      `/listing-submissions/${encodeURIComponent(id)}`,
      { status },
      { signal: options?.signal },
    );
    return data;
  }
}

export const listingsService = new ListingsService(apiClient);
