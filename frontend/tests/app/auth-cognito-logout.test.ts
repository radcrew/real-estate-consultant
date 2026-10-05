import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "../../app/(auth)/auth/cognito-logout/route";

beforeEach(() => {
  vi.stubEnv("COGNITO_DOMAIN", "https://radestate.auth.us-east-1.amazoncognito.com/");
  vi.stubEnv("COGNITO_CLIENT_ID", "client-123");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("cognito logout route", () => {
  it("sends the browser through Cognito's /logout and back home", () => {
    const res = GET(new Request("https://app.test/auth/cognito-logout"));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.origin + location.pathname).toBe(
      "https://radestate.auth.us-east-1.amazoncognito.com/logout",
    );
    expect(Object.fromEntries(location.searchParams)).toEqual({
      client_id: "client-123",
      logout_uri: "https://app.test/",
    });
  });

  it("just goes home when Cognito is not configured", () => {
    vi.stubEnv("COGNITO_DOMAIN", "");
    const res = GET(new Request("https://app.test/auth/cognito-logout"));
    expect(res.headers.get("location")).toBe("https://app.test/");
  });
});
