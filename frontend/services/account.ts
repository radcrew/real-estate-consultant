import type { AxiosInstance } from "axios";

import type { ProfileFormValues } from "@utils/account/validation";
import { apiClient } from "@lib/api-client";

export type AccountProfileResponse = {
  id: string;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  zip_code: string | null;
  country: string | null;
};

export type AccountProfileUpdateBody = Partial<{
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
}>;

export type AccountPasswordChangeBody = {
  current_password: string;
  new_password: string;
};

const FORM_TO_API: { key: keyof ProfileFormValues; api: keyof AccountProfileUpdateBody }[] = [
  { key: "firstName", api: "first_name" },
  { key: "lastName", api: "last_name" },
  { key: "email", api: "email" },
  { key: "phone", api: "phone" },
  { key: "address", api: "address" },
  { key: "city", api: "city" },
  { key: "state", api: "state" },
  { key: "zipCode", api: "zip_code" },
  { key: "country", api: "country" },
];

export const mapProfileResponseToForm = (r: AccountProfileResponse): ProfileFormValues => ({
  firstName: r.first_name ?? "",
  lastName: r.last_name ?? "",
  email: r.email ?? "",
  phone: r.phone ?? "",
  address: r.address ?? "",
  city: r.city ?? "",
  state: r.state ?? "",
  zipCode: r.zip_code ?? "",
  country: r.country ?? "",
});

export const buildProfileUpdateBody = (
  draft: ProfileFormValues,
  baseline: ProfileFormValues,
): AccountProfileUpdateBody => {
  const body: AccountProfileUpdateBody = {};
  for (const { key, api } of FORM_TO_API) {
    const next = draft[key].trim();
    const prev = baseline[key].trim();
    if (next !== prev) {
      (body as Record<string, string>)[api] = next;
    }
  }
  return body;
};

export class AccountService {
  constructor(private readonly http: AxiosInstance) {}

  async getProfile(options?: { signal?: AbortSignal }): Promise<AccountProfileResponse> {
    const { data } = await this.http.get<AccountProfileResponse>("/account/profile", {
      signal: options?.signal,
    });
    return data;
  }

  async updateProfile(
    body: AccountProfileUpdateBody,
    options?: { signal?: AbortSignal },
  ): Promise<AccountProfileResponse> {
    const { data } = await this.http.patch<AccountProfileResponse>("/account/profile", body, {
      signal: options?.signal,
    });
    return data;
  }

  async changePassword(
    body: AccountPasswordChangeBody,
    options?: { signal?: AbortSignal },
  ): Promise<void> {
    await this.http.post("/account/password", body, { signal: options?.signal });
  }
}

export const accountService = new AccountService(apiClient);
