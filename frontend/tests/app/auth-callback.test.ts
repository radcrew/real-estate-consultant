import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GET } from "../../app/(auth)/auth/callback/route";

const mockCookieStore = { get: vi.fn() };

vi.mock("next/headers", () => ({
  cookies: () => Promise.resolve(mockCookieStore),
}));

const CALLBACK = "https://app.test/auth/callback";

const exchangeResponse = {
  access_token: "at",
  id_token: "it",
  refresh_token: "rt",
  expires_in: 3600,
  token_type: "Bearer",
  user: { id: "u1", email: "jane@test.com", username: "google_123" },
};

const fetchMock = vi.fn();

const withState = (state = "s1", next = "/") =>
  mockCookieStore.get.mockReturnValue({ value: JSON.stringify({ state, next }) });

beforeEach(() => {
  vi.clearAllMocks();
  console.error = vi.fn();
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockResolvedValue(new Response(JSON.stringify(exchangeResponse), { status: 200 }));
  withState();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

/** Cookie name -> the raw Set-Cookie line, for max-age assertions. */
const setCookies = (res: Response) =>
  res.headers.getSetCookie().reduce<Record<string, string>>((acc, line) => {
    acc[line.split("=")[0]] = line;
    return acc;
  }, {});

const failure = (res: Response) => {
  const location = new URL(res.headers.get("location") ?? "");
  return {
    path: location.pathname,
    reason: location.searchParams.get("oauth_reason"),
    error: location.searchParams.get("oauth_error"),
  };
};

describe("auth callback route", () => {
  it("exchanges the code on the backend, stores the session and redirects home", async () => {
    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(res.headers.get("location")).toBe("https://app.test/");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/auth\/oauth\/exchange$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ code: "abc", redirect_uri: CALLBACK }),
      }),
    );

    const cookies = setCookies(res);
    // One decode, exactly what readSessionFromCookie does in the browser.
    const raw = cookies["radestate.session"].split(";")[0].slice("radestate.session=".length);
    const stored = JSON.parse(decodeURIComponent(raw));
    expect(stored).toMatchObject({
      accessToken: "at",
      refreshToken: "rt",
      expiresIn: 3600,
      user: { id: "u1", email: "jane@test.com", username: "google_123" },
    });
    expect(stored).not.toHaveProperty("idToken");
    // The one-time state is spent.
    expect(cookies["radestate.oauth_state"]).toMatch(/Max-Age=0/i);
  });

  it("returns to the next path saved when sign-in started", async () => {
    withState("s1", "/account");

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(res.headers.get("location")).toBe("https://app.test/account");
  });

  it("ignores an absolute next path even if one was saved", async () => {
    withState("s1", "//evil.test");

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(res.headers.get("location")).toBe("https://app.test/");
  });

  it("rejects a state that does not match the cookie", async () => {
    const res = await GET(new Request(`${CALLBACK}?code=abc&state=forged`));

    expect(failure(res)).toMatchObject({ path: "/sign-in", reason: "state_mismatch" });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(setCookies(res)["radestate.session"]).toBeUndefined();
  });

  it("rejects a callback with no state cookie", async () => {
    mockCookieStore.get.mockReturnValue(undefined);

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(failure(res).reason).toBe("state_mismatch");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reports a provider error, e.g. the user cancelled at Google", async () => {
    const res = await GET(
      new Request(`${CALLBACK}?error=access_denied&error_description=User+cancelled`),
    );

    expect(failure(res)).toMatchObject({ path: "/sign-in", reason: "provider_error" });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("reports a missing code", async () => {
    const res = await GET(new Request(`${CALLBACK}?state=s1`));

    expect(failure(res)).toMatchObject({
      reason: "missing_code",
      error: "Missing OAuth code. Try signing in again.",
    });
  });

  it("reports a rejected exchange without storing a session", async () => {
    fetchMock.mockResolvedValue(new Response('{"detail":"bad code"}', { status: 400 }));

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(failure(res)).toMatchObject({
      reason: "exchange_failed",
      error: "Sign-in failed. Please try again.",
    });
    expect(setCookies(res)["radestate.session"]).toBeUndefined();
  });

  it("reports an unreachable backend as unexpected", async () => {
    fetchMock.mockRejectedValue(new Error("connect ECONNREFUSED"));

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(failure(res).reason).toBe("unexpected");
  });

  it("keeps the stored session small enough for one cookie", async () => {
    // Realistic Cognito sizes: access ~1.1 KB, refresh ~1.8 KB (the ID token is not stored).
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          ...exchangeResponse,
          access_token: "a".repeat(1100),
          id_token: "i".repeat(1200),
          refresh_token: "r".repeat(1800),
        }),
        { status: 200 },
      ),
    );

    const res = await GET(new Request(`${CALLBACK}?code=abc&state=s1`));

    expect(setCookies(res)["radestate.session"].length).toBeLessThan(4096);
  });
});
