import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type SignInBody = {
  email: string;
  password: string;
};

export type SignInResponse = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  user: { id: string; email: string | null };
};

export type SignUpBody = {
  email: string;
  password: string;
};

export type SignUpResponse = {
  id: string;
  email: string | null;
  created_at: string;
};

export class AuthService {
  constructor(private readonly http: AxiosInstance) {}

  async signIn(body: SignInBody): Promise<SignInResponse> {
    const { data } = await this.http.post<SignInResponse>("/auth/sign-in", body);
    return data;
  }

  async signUp(body: SignUpBody): Promise<SignUpResponse> {
    const { data } = await this.http.post<SignUpResponse>("/auth/sign-up", body);
    return data;
  }
}

/** Default app wiring; pass a custom `AxiosInstance` in tests via `new AuthService(mockHttp)`. */
export const authService = new AuthService(apiClient);
