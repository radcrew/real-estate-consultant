import type { AxiosInstance } from "axios";
import { describe, expect, it, vi } from "vitest";
import { AuthService, toStoredSession } from "@services/auth";
import type { SignInResponse, SignUpResponse } from "@services/auth";

const makeHttp = (data: unknown) =>
  ({ post: vi.fn().mockResolvedValue({ data }) }) as unknown as AxiosInstance;

const signInResponse: SignInResponse = {
  access_token: "tok",
  id_token: "id",
  refresh_token: "ref",
  expires_in: 3600,
  token_type: "Bearer",
  user: { id: "u-1", email: "jane@example.com", username: "u-1" },
};

const signUpResponse: SignUpResponse = {
  id: "u-1",
  email: "jane@example.com",
  confirmation_required: true,
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

  it("confirmSignUp posts the email and code", async () => {
    const http = makeHttp(undefined);
    await new AuthService(http).confirmSignUp("jane@example.com", "123456");
    expect(http.post).toHaveBeenCalledWith("/auth/confirm", {
      email: "jane@example.com",
      code: "123456",
    });
  });

  it("resendCode posts the email", async () => {
    const http = makeHttp(undefined);
    await new AuthService(http).resendCode("jane@example.com");
    expect(http.post).toHaveBeenCalledWith("/auth/resend-code", { email: "jane@example.com" });
  });

  it("refresh posts the refresh token with the Cognito username", async () => {
    const http = makeHttp(signInResponse);
    const data = await new AuthService(http).refresh("ref", "u-1");
    expect(http.post).toHaveBeenCalledWith("/auth/refresh", {
      refresh_token: "ref",
      username: "u-1",
    });
    expect(data).toEqual(signInResponse);
  });

  it("forgotPassword posts the email", async () => {
    const http = makeHttp(undefined);
    await new AuthService(http).forgotPassword("jane@example.com");
    expect(http.post).toHaveBeenCalledWith("/auth/forgot-password", {
      email: "jane@example.com",
    });
  });

  it("resetPassword posts email, code and new password", async () => {
    const http = makeHttp(undefined);
    const body = { email: "jane@example.com", code: "123456", password: "new-secret" };
    await new AuthService(http).resetPassword(body);
    expect(http.post).toHaveBeenCalledWith("/auth/reset-password", body);
  });

  it("signOut posts to /auth/sign-out", async () => {
    const http = makeHttp(undefined);
    await new AuthService(http).signOut();
    expect(http.post).toHaveBeenCalledWith("/auth/sign-out");
  });
});

describe("toStoredSession", () => {
  it("maps the response and leaves the ID token out", () => {
    expect(toStoredSession(signInResponse)).toEqual({
      accessToken: "tok",
      refreshToken: "ref",
      expiresIn: 3600,
      tokenType: "Bearer",
      user: { id: "u-1", email: "jane@example.com", username: "u-1", avatarUrl: undefined },
    });
  });

  it("keeps the avatar from the previous session", () => {
    const previous = toStoredSession(signInResponse);
    previous.user.avatarUrl = "https://example.com/a.png";
    expect(toStoredSession(signInResponse, previous).user.avatarUrl).toBe(
      "https://example.com/a.png",
    );
  });
});
