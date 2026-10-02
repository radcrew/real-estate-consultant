import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "../../app/(auth)/auth/google/route";

const START = "https://app.test/auth/google";

beforeEach(() => {
  console.error = vi.fn();
  vi.stubEnv("COGNITO_DOMAIN", "https://radestate.auth.us-east-1.amazoncognito.com/");
  vi.stubEnv("COGNITO_CLIENT_ID", "client-123");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

const stateCookie = (res: Response) =>
  res.headers.getSetCookie().find((line) => line.startsWith("radestate.oauth_state="));

describe("google sign-in start route", () => {
  it("redirects to the Cognito Hosted UI for Google", () => {
    const res = GET(new Request(START));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.origin + location.pathname).toBe(
      "https://radestate.auth.us-east-1.amazoncognito.com/oauth2/authorize",
    );
    expect(Object.fromEntries(location.searchParams)).toMatchObject({
      response_type: "code",
      client_id: "client-123",
      redirect_uri: "https://app.test/auth/callback",
      identity_provider: "Google",
    });
  });

  it("asks only for scopes the app client allows", () => {
    const res = GET(new Request(START));
    const scope = new URL(res.headers.get("location") ?? "").searchParams.get("scope");

    expect(scope).toBe("openid email profile");
  });

  it("stores the same state it sends, in an HttpOnly cookie scoped to the callback", () => {
    const res = GET(new Request(START));
    const sent = new URL(res.headers.get("location") ?? "").searchParams.get("state");
    const cookie = stateCookie(res) ?? "";
    const saved = JSON.parse(decodeURIComponent(cookie.split(";")[0].split("=")[1]));

    expect(saved.state).toBe(sent);
    expect(cookie).toMatch(/HttpOnly/i);
    expect(cookie).toMatch(/Path=\/auth\/callback/i);
    expect(cookie).toMatch(/Secure/i);
  });

  it("remembers a relative next path and drops an absolute one", () => {
    const keep = stateCookie(GET(new Request(`${START}?next=%2Faccount`))) ?? "";
    const drop = stateCookie(GET(new Request(`${START}?next=%2F%2Fevil.test`))) ?? "";

    expect(decodeURIComponent(keep)).toContain('"next":"/account"');
    expect(decodeURIComponent(drop)).toContain('"next":"/"');
  });

  it("sends the user back to sign-in when Cognito is not configured", () => {
    vi.stubEnv("COGNITO_DOMAIN", "");

    const res = GET(new Request(START));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.pathname).toBe("/sign-in");
    expect(location.searchParams.get("oauth_reason")).toBe("not_configured");
    expect(stateCookie(res)).toBeUndefined();
  });
});
