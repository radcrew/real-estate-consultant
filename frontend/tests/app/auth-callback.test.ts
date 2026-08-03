import { describe, expect, it, vi, beforeEach } from "vitest";

import { GET } from "../../app/(auth)/auth/callback/route";

const mockExchange = vi.fn();
const mockCookieStore = { getAll: vi.fn() };

vi.mock("next/headers", () => ({
  cookies: () => Promise.resolve(mockCookieStore),
}));

vi.mock("@lib/supabase-server", () => ({
  getSupabaseServerClient: () =>
    Promise.resolve({ auth: { exchangeCodeForSession: (code: string) => mockExchange(code) } }),
}));

vi.mock("@lib/oauth-profile-sync", () => ({
  syncProfileNamesAfterOAuth: vi.fn().mockResolvedValue(undefined),
}));

const CALLBACK = "https://app.test/auth/callback";

const session = (overrides: Record<string, unknown> = {}) => ({
  access_token: "at",
  refresh_token: "rt",
  token_type: "bearer",
  user: { id: "u1", email: "jane@test.com" },
  ...overrides,
});

beforeEach(() => {
  vi.clearAllMocks();
  console.error = vi.fn();
  // The stale PKCE verifier a failed attempt would otherwise leave behind.
  mockCookieStore.getAll.mockReturnValue([
    { name: "sb-abc-auth-token-code-verifier", value: "v" },
    { name: "sb-abc-auth-token.0", value: "chunk" },
    { name: "radestate.session", value: "keep-me" },
  ]);
});

/** Cookie name -> the raw Set-Cookie line, for max-age assertions. */
const setCookies = (res: Response) =>
  res.headers.getSetCookie().reduce<Record<string, string>>((acc, line) => {
    acc[line.split("=")[0]] = line;
    return acc;
  }, {});

describe("auth callback route", () => {
  it("stores the session and redirects home on success", async () => {
    mockExchange.mockResolvedValue({ data: { session: session() }, error: null });

    const res = await GET(new Request(`${CALLBACK}?code=abc`));

    expect(res.headers.get("location")).toBe("https://app.test/");
    expect(setCookies(res)["radestate.session"]).toBeDefined();
  });

  it("honours a relative next path", async () => {
    mockExchange.mockResolvedValue({ data: { session: session() }, error: null });

    const res = await GET(new Request(`${CALLBACK}?code=abc&next=%2Faccount`));

    expect(res.headers.get("location")).toBe("https://app.test/account");
  });

  it("rejects an absolute next path", async () => {
    mockExchange.mockResolvedValue({ data: { session: session() }, error: null });

    const res = await GET(new Request(`${CALLBACK}?code=abc&next=%2F%2Fevil.test`));

    expect(res.headers.get("location")).toBe("https://app.test/");
  });

  it("reports the reason when the exchange errors", async () => {
    mockExchange.mockResolvedValue({ data: {}, error: { message: "bad verifier" } });

    const res = await GET(new Request(`${CALLBACK}?code=abc`));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.pathname).toBe("/sign-in");
    expect(location.searchParams.get("oauth_reason")).toBe("exchange_failed");
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining("bad verifier"));
  });

  // Previously this branch returned the generic error and logged nothing at all.
  it("reports a missing refresh token instead of failing silently", async () => {
    mockExchange.mockResolvedValue({
      data: { session: session({ refresh_token: undefined }) },
      error: null,
    });

    const res = await GET(new Request(`${CALLBACK}?code=abc`));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.searchParams.get("oauth_reason")).toBe("no_refresh_token");
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining("no_refresh_token"));
  });

  it("reports an unexpected throw", async () => {
    mockExchange.mockRejectedValue(new Error("boom"));

    const res = await GET(new Request(`${CALLBACK}?code=abc`));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.searchParams.get("oauth_reason")).toBe("unexpected");
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining("boom"));
  });

  it("reports a missing code without calling Supabase", async () => {
    const res = await GET(new Request(CALLBACK));
    const location = new URL(res.headers.get("location") ?? "");

    expect(location.searchParams.get("oauth_reason")).toBe("missing_code");
    expect(mockExchange).not.toHaveBeenCalled();
  });

  it("expires stale supabase cookies on failure so the retry starts clean", async () => {
    mockExchange.mockResolvedValue({ data: {}, error: { message: "bad verifier" } });

    const res = await GET(new Request(`${CALLBACK}?code=abc`));
    const cookies = setCookies(res);

    expect(cookies["sb-abc-auth-token-code-verifier"]).toContain("Max-Age=0");
    expect(cookies["sb-abc-auth-token.0"]).toContain("Max-Age=0");
    // Only Supabase's own cookies are cleared.
    expect(cookies["radestate.session"]).toBeUndefined();
  });

  it("leaves supabase cookies alone on success", async () => {
    mockExchange.mockResolvedValue({ data: { session: session() }, error: null });

    const res = await GET(new Request(`${CALLBACK}?code=abc`));

    expect(setCookies(res)["sb-abc-auth-token-code-verifier"]).toBeUndefined();
  });
});
