import { apiClient } from "@/lib/api-client";

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
  static async signIn(body: SignInBody): Promise<SignInResponse> {
    const { data } = await apiClient.post<SignInResponse>("/auth/sign-in", body);
    return data;
  }

  static async signUp(body: SignUpBody): Promise<SignUpResponse> {
    const { data } = await apiClient.post<SignUpResponse>("/auth/sign-up", body);
    return data;
  }
}
