import { beforeEach, describe, expect, it, vi } from "vitest";
import { syncProfileNamesAfterOAuth } from "@lib/oauth-profile-sync";
import type { SupabaseClient, User as AuthUser } from "@supabase/supabase-js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeUser = (overrides: Partial<AuthUser> = {}): AuthUser =>
  ({
    id: "user-1",
    email: "jane@example.com",
    user_metadata: { given_name: "Jane", family_name: "Doe" },
    ...overrides,
  }) as AuthUser;

type MockChain = {
  select: ReturnType<typeof vi.fn>;
  eq: ReturnType<typeof vi.fn>;
  maybeSingle: ReturnType<typeof vi.fn>;
  update: ReturnType<typeof vi.fn>;
  insert: ReturnType<typeof vi.fn>;
};

const makeMockSupabase = (selectResult: unknown, mutateResult: unknown = { error: null }) => {
  const chain: MockChain = {
    select: vi.fn(),
    eq: vi.fn(),
    maybeSingle: vi.fn().mockResolvedValue(selectResult),
    update: vi.fn().mockReturnValue({ eq: vi.fn().mockResolvedValue(mutateResult) }),
    insert: vi.fn().mockResolvedValue(mutateResult),
  };
  chain.select.mockReturnValue(chain);
  chain.eq.mockReturnValue(chain);

  return {
    from: vi.fn().mockReturnValue(chain),
    _chain: chain,
  } as unknown as SupabaseClient & { _chain: MockChain };
};

// ---------------------------------------------------------------------------
// Early-exit cases
// ---------------------------------------------------------------------------

describe("syncProfileNamesAfterOAuth", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("does nothing when user has no google names and no email", async () => {
    const supabase = makeMockSupabase({ data: null, error: null });
    const user = makeUser({ user_metadata: {}, email: undefined });
    await syncProfileNamesAfterOAuth(supabase, user);
    expect(supabase.from).not.toHaveBeenCalled();
  });

  it("proceeds when only email is present (no google names)", async () => {
    const supabase = makeMockSupabase({ data: null, error: null });
    const user = makeUser({ user_metadata: {}, email: "anon@example.com" });
    await syncProfileNamesAfterOAuth(supabase, user);
    expect(supabase.from).toHaveBeenCalledWith("profiles");
  });

  // -------------------------------------------------------------------------
  // Select failure
  // -------------------------------------------------------------------------

  it("returns early and logs when the select query fails", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const supabase = makeMockSupabase({ data: null, error: { message: "db error" } });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(consoleError).toHaveBeenCalledWith(
      expect.stringContaining("[oauth]"),
      "db error",
    );
  });

  // -------------------------------------------------------------------------
  // Insert path (no existing profile)
  // -------------------------------------------------------------------------

  it("inserts a new profile when none exists", async () => {
    const supabase = makeMockSupabase({ data: null, error: null });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(supabase._chain.insert).toHaveBeenCalledWith(
      expect.objectContaining({ id: "user-1", email: "jane@example.com" }),
    );
  });

  it("inserts with google names when no existing profile", async () => {
    const supabase = makeMockSupabase({ data: null, error: null });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(supabase._chain.insert).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: "Jane", last_name: "Doe" }),
    );
  });

  it("logs when insert fails", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const supabase = makeMockSupabase(
      { data: null, error: null },
      { error: { message: "insert failed" } },
    );
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(consoleError).toHaveBeenCalledWith(expect.stringContaining("[oauth]"), "insert failed");
  });

  // -------------------------------------------------------------------------
  // Update path (existing profile)
  // -------------------------------------------------------------------------

  it("updates an existing profile instead of inserting", async () => {
    const supabase = makeMockSupabase({
      data: { first_name: "Janet", last_name: null },
      error: null,
    });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(supabase._chain.update).toHaveBeenCalled();
    expect(supabase._chain.insert).not.toHaveBeenCalled();
  });

  it("preserves existing first_name over the oauth value", async () => {
    const supabase = makeMockSupabase({
      data: { first_name: "Janet", last_name: null },
      error: null,
    });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(supabase._chain.update).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: "Janet" }),
    );
  });

  it("fills in a null existing name with the oauth value", async () => {
    const supabase = makeMockSupabase({
      data: { first_name: null, last_name: null },
      error: null,
    });
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(supabase._chain.update).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: "Jane", last_name: "Doe" }),
    );
  });

  it("logs when update fails", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const supabase = makeMockSupabase(
      { data: { first_name: null, last_name: null }, error: null },
      { error: { message: "update failed" } },
    );
    await syncProfileNamesAfterOAuth(supabase, makeUser());
    expect(consoleError).toHaveBeenCalledWith(expect.stringContaining("[oauth]"), "update failed");
  });
});
