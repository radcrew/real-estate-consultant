import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET as logout } from "../../app/(auth)/auth/cognito-logout/route";
import { GET as logoutDone } from "../../app/(auth)/auth/cognito-logout/done/route";

beforeEach(() => {
  vi.stubEnv("COGNITO_DOMAIN", "https://radestate.auth.us-east-1.amazoncognito.com/");
  vi.stubEnv("COGNITO_CLIENT_ID", "client-123");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

/** The after-logout cookie's value, from the Set-Cookie header. */
const afterLogoutCookie = (res: Response) =>
  res.headers
    .getSetCookie()
    .find((line) => line.startsWith("radestate.after_logout="))
    ?.split(";")[0]
    .slice("radestate.after_logout=".length);

describe("cognito logout route", () => {
  const logoutParams = (res: Response) => {
    const location = new URL(res.headers.get("location") ?? "");
    expect(location.origin + location.pathname).toBe(
      "https://radestate.auth.us-east-1.amazoncognito.com/logout",
    );
    return Object.fromEntries(location.searchParams);
  };

  it("sends the browser through Cognito's /logout and straight back home", () => {
    const res = logout(new Request("https://app.test/auth/cognito-logout"));
    expect(logoutParams(res)).toEqual({
      client_id: "client-123",
      logout_uri: "https://app.test/",
    });
    expect(afterLogoutCookie(res)).toBeUndefined();
  });

  it("returns through the done route to keep a same-site next path", () => {
    const res = logout(new Request("https://app.test/auth/cognito-logout?next=%2Fsaved"));
    expect(logoutParams(res).logout_uri).toBe("https://app.test/auth/cognito-logout/done");
    expect(decodeURIComponent(afterLogoutCookie(res) ?? "")).toBe("/saved");
  });

  it("drops a next that points off-site and goes home", () => {
    const res = logout(
      new Request("https://app.test/auth/cognito-logout?next=https%3A%2F%2Fevil.test"),
    );
    expect(logoutParams(res).logout_uri).toBe("https://app.test/");
  });

  it("goes straight to next when Cognito is not configured", () => {
    vi.stubEnv("COGNITO_DOMAIN", "");
    const res = logout(new Request("https://app.test/auth/cognito-logout?next=%2Fsaved"));
    expect(res.headers.get("location")).toBe("https://app.test/saved");
  });
});

describe("cognito logout done route", () => {
  const done = (cookie?: string) =>
    logoutDone(
      new Request("https://app.test/auth/cognito-logout/done", {
        headers: cookie ? { cookie } : {},
      }),
    );

  it("continues to the saved path and clears the cookie", () => {
    const res = done("radestate.after_logout=%2Fsaved");
    expect(res.headers.get("location")).toBe("https://app.test/saved");
    expect(afterLogoutCookie(res)).toBe("");
  });

  it("goes home without a saved path", () => {
    expect(done().headers.get("location")).toBe("https://app.test/");
  });

  it("goes home if the saved path points off-site", () => {
    const res = done("radestate.after_logout=%2F%2Fevil.test");
    expect(res.headers.get("location")).toBe("https://app.test/");
  });
});
