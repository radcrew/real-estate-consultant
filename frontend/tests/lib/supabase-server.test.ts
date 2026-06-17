import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(() => ({ _isMock: true })),
}));

vi.mock("next/headers", () => ({
  cookies: vi.fn(),
}));

describe("getSupabaseServerClient", () => {
  const originalEnv: Record<string, unknown> = {};

  beforeEach(async () => {
    vi.resetModules();
    const { createServerClient } = await import("@supabase/ssr");
    vi.mocked(createServerClient).mockReturnValue({ _isMock: true } as never);

    const { cookies } = await import("next/headers");
    const mockCookieStore = {
      getAll: vi.fn(() => [{ name: "sb-token", value: "abc" }]),
      set: vi.fn(),
    };
    vi.mocked(cookies).mockResolvedValue(mockCookieStore as never);

    originalEnv.SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL;
    originalEnv.SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  });

  afterEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = originalEnv.SUPABASE_URL as string;
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = originalEnv.SUPABASE_ANON_KEY as string;
  });

  it("throws when SUPABASE_URL is missing", async () => {
    vi.doMock("@config/env", () => ({ SUPABASE_URL: "", SUPABASE_ANON_KEY: "key" }));
    const { getSupabaseServerClient } = await import("@lib/supabase-server");
    await expect(getSupabaseServerClient()).rejects.toThrow(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  });

  it("throws when SUPABASE_ANON_KEY is missing", async () => {
    vi.doMock("@config/env", () => ({ SUPABASE_URL: "https://x.supabase.co", SUPABASE_ANON_KEY: "" }));
    const { getSupabaseServerClient } = await import("@lib/supabase-server");
    await expect(getSupabaseServerClient()).rejects.toThrow(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  });

  it("calls createServerClient with correct URL and key", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://test.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    }));
    const { getSupabaseServerClient } = await import("@lib/supabase-server");
    await getSupabaseServerClient();
    const { createServerClient } = await import("@supabase/ssr");
    expect(vi.mocked(createServerClient)).toHaveBeenCalledWith(
      "https://test.supabase.co",
      "anon-key",
      expect.objectContaining({ cookies: expect.any(Object) }),
    );
  });

  it("returns the supabase client", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://test.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    }));
    const { getSupabaseServerClient } = await import("@lib/supabase-server");
    const client = await getSupabaseServerClient();
    expect(client).toEqual({ _isMock: true });
  });
});
