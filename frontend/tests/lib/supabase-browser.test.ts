// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the Supabase SSR factory so tests never hit the network
vi.mock("@supabase/ssr", () => ({
  createBrowserClient: vi.fn(() => ({ _isMock: true })),
}));

// ---------------------------------------------------------------------------
// Each test gets a fresh module (resets the singleton + env var binding)
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.resetModules();
});

describe("getSupabaseBrowserClient", () => {
  it("throws when SUPABASE_URL is missing", async () => {
    vi.doMock("@config/env", () => ({ SUPABASE_URL: "", SUPABASE_ANON_KEY: "anon-key" }));
    const { getSupabaseBrowserClient } = await import("@lib/supabase-browser");
    expect(() => getSupabaseBrowserClient()).toThrow(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  });

  it("throws when SUPABASE_ANON_KEY is missing", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://example.supabase.co",
      SUPABASE_ANON_KEY: "",
    }));
    const { getSupabaseBrowserClient } = await import("@lib/supabase-browser");
    expect(() => getSupabaseBrowserClient()).toThrow(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  });

  it("returns a client when both env vars are present", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://example.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    }));
    const { getSupabaseBrowserClient } = await import("@lib/supabase-browser");
    expect(getSupabaseBrowserClient()).toBeDefined();
  });

  it("returns the same instance on repeated calls (singleton)", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://example.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    }));
    const { getSupabaseBrowserClient } = await import("@lib/supabase-browser");
    expect(getSupabaseBrowserClient()).toBe(getSupabaseBrowserClient());
  });

  it("calls createBrowserClient only once across repeated calls", async () => {
    vi.doMock("@config/env", () => ({
      SUPABASE_URL: "https://example.supabase.co",
      SUPABASE_ANON_KEY: "anon-key",
    }));
    const { createBrowserClient } = await import("@supabase/ssr");
    vi.mocked(createBrowserClient).mockClear();

    const { getSupabaseBrowserClient } = await import("@lib/supabase-browser");
    getSupabaseBrowserClient();
    getSupabaseBrowserClient();
    getSupabaseBrowserClient();

    expect(vi.mocked(createBrowserClient)).toHaveBeenCalledOnce();
  });
});
