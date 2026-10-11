// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));
vi.mock("@services/auth", () => ({
  authService: { signOut: vi.fn().mockResolvedValue(undefined) },
}));
vi.mock("@services/account", () => ({
  accountService: { getProfile: vi.fn().mockResolvedValue({ avatar_url: null }) },
}));

import { AuthProvider, useAuth } from "@contexts/auth";
import { readSession, saveSession } from "@lib/auth-session";
import { authService } from "@services/auth";

const wrapper = ({ children }: { children: ReactNode }) => <AuthProvider>{children}</AuthProvider>;

const mockAssign = vi.fn();

beforeEach(() => {
  vi.spyOn(window, "location", "get").mockReturnValue({
    assign: mockAssign,
  } as unknown as Location);
});

const signIn = () =>
  saveSession({
    accessToken: "access-tok",
    refreshToken: "refresh-tok",
    expiresIn: 3600,
    tokenType: "Bearer",
    user: { id: "u1", email: "a@b.com", username: "u1", avatarUrl: "x" },
  });

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  sessionStorage.clear();
  document.cookie = "radestate.session=; Path=/; Max-Age=0; SameSite=Lax";
  vi.clearAllMocks();
});

describe("AuthProvider signOut", () => {
  it("revokes the tokens, clears the session, then ends the Cognito session", async () => {
    signIn();
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(() => result.current.signOut());

    expect(authService.signOut).toHaveBeenCalledWith("access-tok");
    expect(readSession()).toBeNull();
    // Without Cognito's /logout, the next Google sign-in here reuses this account.
    expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout");
  });

  it("does not wait forever for a revoke that hangs", async () => {
    vi.useFakeTimers();
    vi.mocked(authService.signOut).mockReturnValueOnce(new Promise(() => {}));
    signIn();
    const { result } = renderHook(() => useAuth(), { wrapper });

    let done: Promise<void> | undefined;
    act(() => {
      done = result.current.signOut();
    });
    expect(mockAssign).not.toHaveBeenCalled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
      await done;
    });

    expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout");
  });

  it("still ends the Cognito session when there is no local session", async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(() => result.current.signOut());

    expect(authService.signOut).not.toHaveBeenCalled();
    expect(readSession()).toBeNull();
    expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout");
  });
});
