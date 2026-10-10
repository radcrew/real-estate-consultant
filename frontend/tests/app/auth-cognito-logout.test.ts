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
  it("sends the browser through Cognito's /logout and back to the done route", () => {
    const res = logout(new Request("https://app.test/auth/cognito-logout"));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.origin + location.pathname).toBe(
      "https://radestate.auth.us-east-1.amazoncognito.com/logout",
    );
    expect(Object.fromEntries(location.searchParams)).toEqual({
      client_id: "client-123",
      logout_uri: "https://app.test/auth/cognito-logout/done",
    });
    expect(afterLogoutCookie(res)).toBe(encodeURIComponent("/"));
  });

  it("keeps a same-site next path for after the logout", () => {
    const res = logout(new Request("https://app.test/auth/cognito-logout?next=%2Fsaved"));
    expect(decodeURIComponent(afterLogoutCookie(res) ?? "")).toBe("/saved");
  });

  it("drops a next that points off-site", () => {
    const res = logout(
      new Request("https://app.test/auth/cognito-logout?next=https%3A%2F%2Fevil.test"),
    );
    expect(decodeURIComponent(afterLogoutCookie(res) ?? "")).toBe("/");
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
