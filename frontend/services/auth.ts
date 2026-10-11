import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";

export type SignInBody = {
  email: string;
  password: string;
};

export type SignInResponse = {
  access_token: string;
  id_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  // username is Cognito's user name; /auth/refresh needs it back.
  user: { id: string; email: string | null; username: string };
};

/** Body of POST /auth/refresh. The api-client interceptor is its only caller. */
export type RefreshRequestBody = {
  refresh_token: string;
  username: string;
};

export type SignUpBody = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
};

export type SignUpResponse = {
  id: string;
  email: string | null;
  // True until the emailed code is submitted to /auth/confirm.
  confirmation_required: boolean;
};

export type ResetPasswordBody = {
  email: string;
  code: string;
  password: string;
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

  async confirmSignUp(email: string, code: string): Promise<void> {
    await this.http.post("/auth/confirm", { email, code });
  }

  async resendCode(email: string): Promise<void> {
    await this.http.post("/auth/resend-code", { email });
  }

  async forgotPassword(email: string): Promise<void> {
    await this.http.post("/auth/forgot-password", { email });
  }

  async resetPassword(body: ResetPasswordBody): Promise<void> {
    await this.http.post("/auth/reset-password", body);
  }

  /** Takes the token explicitly: the caller clears the session before this request runs. */
  async signOut(accessToken: string): Promise<void> {
    await this.http.post("/auth/sign-out", undefined, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  }
}

export const authService = new AuthService(apiClient);
