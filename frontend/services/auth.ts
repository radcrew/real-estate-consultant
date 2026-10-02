import type { AxiosInstance } from "axios";

import { apiClient } from "@lib/api-client";
import type { StoredSession } from "@lib/auth-session";

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

/**
 * Map a sign-in, refresh or Google exchange response to the stored session.
 *
 * The ID token is left out on purpose: the session is mirrored to a cookie, and Cognito's
 * three tokens together exceed the ~4 KB browser cookie limit. Nothing reads it.
 */
export const toStoredSession = (
  data: SignInResponse,
  previous?: StoredSession | null,
): StoredSession => ({
  accessToken: data.access_token,
  refreshToken: data.refresh_token,
  expiresIn: data.expires_in,
  tokenType: data.token_type,
  user: {
    id: data.user.id,
    email: data.user.email,
    username: data.user.username,
    avatarUrl: previous?.user.avatarUrl,
  },
});

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

  async refresh(refreshToken: string, username: string): Promise<SignInResponse> {
    const { data } = await this.http.post<SignInResponse>("/auth/refresh", {
      refresh_token: refreshToken,
      username,
    });
    return data;
  }

  async forgotPassword(email: string): Promise<void> {
    await this.http.post("/auth/forgot-password", { email });
  }

  async resetPassword(body: ResetPasswordBody): Promise<void> {
    await this.http.post("/auth/reset-password", body);
  }

  async signOut(): Promise<void> {
    await this.http.post("/auth/sign-out");
  }
}

export const authService = new AuthService(apiClient);
