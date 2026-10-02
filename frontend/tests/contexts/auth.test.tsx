// @vitest-environment jsdom
import { act, renderHook } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

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

afterEach(() => {
  sessionStorage.clear();
  document.cookie = "radestate.session=; Path=/; Max-Age=0; SameSite=Lax";
  vi.clearAllMocks();
});

describe("AuthProvider signOut", () => {
  it("revokes the tokens with the current access token and clears the session", () => {
    saveSession({
      accessToken: "access-tok",
      refreshToken: "refresh-tok",
      expiresIn: 3600,
      tokenType: "Bearer",
      user: { id: "u1", email: "a@b.com", username: "u1", avatarUrl: "x" },
    });
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => result.current.signOut());

    expect(authService.signOut).toHaveBeenCalledWith("access-tok");
    expect(readSession()).toBeNull();
  });

  it("only clears locally when there is no session", () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    act(() => result.current.signOut());

    expect(authService.signOut).not.toHaveBeenCalled();
    expect(readSession()).toBeNull();
  });
});
