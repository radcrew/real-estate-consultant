import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { AuthService } from "@services/auth";
import type { SignInResponse, SignUpResponse } from "@services/auth";

const makeHttp = (data: unknown) =>
  ({ post: vi.fn().mockResolvedValue({ data }) }) as unknown as AxiosInstance;

const signInResponse: SignInResponse = {
  access_token: "tok",
  refresh_token: "ref",
  expires_in: 3600,
  token_type: "bearer",
  user: { id: "u-1", email: "jane@example.com" },
};

const signUpResponse: SignUpResponse = {
  id: "u-1",
  email: "jane@example.com",
  created_at: "2024-01-01T00:00:00Z",
};

describe("AuthService", () => {
  describe("signIn", () => {
    it("calls POST /auth/sign-in with credentials and returns data", async () => {
      const http = makeHttp(signInResponse);
      const body = { email: "jane@example.com", password: "secret" };
      const data = await new AuthService(http).signIn(body);
      expect(http.post).toHaveBeenCalledWith("/auth/sign-in", body);
      expect(data).toEqual(signInResponse);
    });
  });

  describe("signUp", () => {
    it("calls POST /auth/sign-up with registration fields and returns data", async () => {
      const http = makeHttp(signUpResponse);
      const body = {
        email: "jane@example.com",
        password: "secret",
        first_name: "Jane",
        last_name: "Doe",
      };
      const data = await new AuthService(http).signUp(body);
      expect(http.post).toHaveBeenCalledWith("/auth/sign-up", body);
      expect(data).toEqual(signUpResponse);
    });
  });
});
