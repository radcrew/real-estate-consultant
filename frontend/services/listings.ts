import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";
import type { SearchProperty } from "@services/search";

export type ListingProperty = SearchProperty;

export type ListingDetailResponse = {
  property: ListingProperty;
  images: string[];
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
}

export const listingsService = new ListingsService(apiClient);
