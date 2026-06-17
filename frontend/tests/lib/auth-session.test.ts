// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  AUTH_SESSION_CHANGED_EVENT,
  clearSession,
  readSession,
  saveSession,
} from "@lib/auth-session";
import type { StoredSession } from "@lib/auth-session";

const session: StoredSession = {
  accessToken: "access-abc",
  refreshToken: "refresh-xyz",
  expiresIn: 3600,
  tokenType: "bearer",
  user: { id: "user-1", email: "jane@example.com", avatarUrl: null },
};

const session2: StoredSession = { ...session, accessToken: "access-def" };

afterEach(() => {
  sessionStorage.clear();
  // Clear the session cookie between tests
  document.cookie = "radestate.session=; Path=/; Max-Age=0; SameSite=Lax";
});

// ---------------------------------------------------------------------------
// saveSession
// ---------------------------------------------------------------------------

describe("saveSession", () => {
  it("persists the session to sessionStorage", () => {
    saveSession(session);
    const stored = sessionStorage.getItem("radestate.session");
    expect(JSON.parse(stored!)).toEqual(session);
  });

  it("writes a cookie containing the encoded session", () => {
    saveSession(session);
    expect(document.cookie).toContain("radestate.session=");
  });

  it("dispatches the session-changed event", () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
    saveSession(session);
    window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
    expect(listener).toHaveBeenCalledOnce();
  });

  it("overwrites a previously saved session", () => {
    saveSession(session);
    saveSession(session2);
    expect(JSON.parse(sessionStorage.getItem("radestate.session")!)).toEqual(session2);
  });
});

// ---------------------------------------------------------------------------
// clearSession
// ---------------------------------------------------------------------------

describe("clearSession", () => {
  it("removes the session from sessionStorage", () => {
    saveSession(session);
    clearSession();
    expect(sessionStorage.getItem("radestate.session")).toBeNull();
  });

  it("dispatches the session-changed event", () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
    clearSession();
    window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, listener);
    expect(listener).toHaveBeenCalledOnce();
  });

  it("is a no-op when nothing was saved", () => {
    expect(() => clearSession()).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// readSession
// ---------------------------------------------------------------------------

describe("readSession", () => {
  it("returns null when nothing is stored", () => {
    expect(readSession()).toBeNull();
  });

  it("returns the session saved to sessionStorage", () => {
    saveSession(session);
    expect(readSession()).toEqual(session);
  });

  it("returns null after the session is cleared", () => {
    saveSession(session);
    clearSession();
    expect(readSession()).toBeNull();
  });

  it("hydrates sessionStorage from cookie when sessionStorage is empty", () => {
    // Write cookie directly, bypassing sessionStorage
    document.cookie = `radestate.session=${encodeURIComponent(JSON.stringify(session))}; Path=/; Max-Age=604800; SameSite=Lax`;
    sessionStorage.clear();

    const result = readSession();
    expect(result).toEqual(session);
    // Should now be cached in sessionStorage
    expect(sessionStorage.getItem("radestate.session")).not.toBeNull();
  });

  it("returns null for corrupt sessionStorage JSON", () => {
    sessionStorage.setItem("radestate.session", "not-json{{{");
    expect(readSession()).toBeNull();
  });
});
