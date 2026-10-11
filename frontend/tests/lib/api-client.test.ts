// @vitest-environment jsdom
import axios from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock auth-session before importing api-client so the interceptors pick up the mock
vi.mock("@lib/auth-session", async (importOriginal) => ({
  readSession: vi.fn(),
  clearSession: vi.fn(),
  saveSession: vi.fn(),
  toStoredSession: (await importOriginal<typeof import("@lib/auth-session")>()).toStoredSession,
}));

import { readSession, clearSession, saveSession } from "@lib/auth-session";
import type { StoredSession } from "@lib/auth-session";
import { apiClient } from "@lib/api-client";

const mockReadSession = vi.mocked(readSession);
const mockClearSession = vi.mocked(clearSession);
const mockSaveSession = vi.mocked(saveSession);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeResponse = (status: number, data: unknown = {}, config?: Record<string, unknown>) =>
  new axios.AxiosError("Request failed", String(status), config as never, undefined, {
    status,
    data,
    headers: {},
    config: {} as never,
    statusText: String(status),
  });

// ---------------------------------------------------------------------------
// Request interceptor — Authorization header
// ---------------------------------------------------------------------------

describe("apiClient request interceptor", () => {
  afterEach(() => vi.clearAllMocks());

  it("attaches Bearer token when a session exists", async () => {
    mockReadSession.mockReturnValue({
      accessToken: "tok-abc",
      refreshToken: "ref",
      expiresIn: 3600,
      tokenType: "bearer",
      user: { id: "u1", email: "a@b.com" },
    });

    // Run the request interceptor directly
    const handler = apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: unknown) => unknown }>;
    };
    const config = { headers: { set: vi.fn() } };
    handler.handlers[0].fulfilled(config);

    expect(config.headers.set).toHaveBeenCalledWith("Authorization", "Bearer tok-abc");
  });

  it("does not attach Authorization when there is no session", async () => {
    mockReadSession.mockReturnValue(null);

    const handler = apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: unknown) => unknown }>;
    };
    const config = { headers: { set: vi.fn() } };
    handler.handlers[0].fulfilled(config);

    expect(config.headers.set).not.toHaveBeenCalled();
  });

  it("does not attach Authorization when accessToken is empty", async () => {
    mockReadSession.mockReturnValue({
      accessToken: "",
      refreshToken: "ref",
      expiresIn: 3600,
      tokenType: "bearer",
      user: { id: "u1", email: "a@b.com" },
    });

    const handler = apiClient.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (c: unknown) => unknown }>;
    };
    const config = { headers: { set: vi.fn() } };
    handler.handlers[0].fulfilled(config);

    expect(config.headers.set).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Response interceptor — 401 handling
// ---------------------------------------------------------------------------

describe("apiClient response interceptor", () => {
  let originalLocation: Location;

  beforeEach(() => {
    originalLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: { href: "", pathname: "/search", search: "?q=1" },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
    vi.clearAllMocks();
  });

  const getErrorHandler = () => {
    const handler = apiClient.interceptors.response as unknown as {
      handlers: Array<{ rejected: (e: unknown) => unknown }>;
    };
    return handler.handlers[0].rejected;
  };

  it("clears the session on a 401 response", async () => {
    const reject = getErrorHandler();
    await expect(reject(makeResponse(401))).rejects.toBeDefined();
    expect(mockClearSession).toHaveBeenCalledOnce();
  });

  it("redirects to /sign-in with next param on 401", async () => {
    const reject = getErrorHandler();
    await expect(reject(makeResponse(401))).rejects.toBeDefined();
    expect(window.location.href).toBe(
      `/sign-in?next=${encodeURIComponent("/search?q=1")}`,
    );
  });

  it("does not clear session for non-401 errors", async () => {
    const reject = getErrorHandler();
    await expect(reject(makeResponse(403))).rejects.toBeDefined();
    expect(mockClearSession).not.toHaveBeenCalled();
  });

  it("re-rejects the error for non-401 responses", async () => {
    const reject = getErrorHandler();
    const err = makeResponse(500);
    await expect(reject(err)).rejects.toBe(err);
  });

  it("re-rejects the error even on 401", async () => {
    const reject = getErrorHandler();
    const err = makeResponse(401);
    await expect(reject(err)).rejects.toBe(err);
  });
});

// ---------------------------------------------------------------------------
// Response interceptor — refresh once, then retry
// ---------------------------------------------------------------------------

describe("apiClient refresh on 401", () => {
  let originalLocation: Location;
  const session: StoredSession = {
    accessToken: "old-access",
    refreshToken: "refresh-tok",
    expiresIn: 3600,
    tokenType: "Bearer",
    user: { id: "u1", email: "a@b.com", username: "u1", avatarUrl: "https://x/a.png" },
  };
  const refreshed = {
    access_token: "new-access",
    id_token: "id",
    refresh_token: "refresh-tok",
    expires_in: 3600,
    token_type: "Bearer",
    user: { id: "u1", email: "a@b.com", username: "u1" },
  };

  beforeEach(() => {
    originalLocation = window.location;
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: { href: "", pathname: "/search", search: "" },
    });
    mockReadSession.mockReturnValue(session);
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  const reject = (err: unknown) => {
    const handler = apiClient.interceptors.response as unknown as {
      handlers: Array<{ rejected: (e: unknown) => Promise<unknown> }>;
    };
    return handler.handlers[0].rejected(err);
  };

  it("refreshes, saves the new session and retries the request", async () => {
    const post = vi.spyOn(axios, "post").mockResolvedValue({ data: refreshed });
    const retry = vi.spyOn(apiClient, "request").mockResolvedValue({ data: "ok" });

    await expect(reject(makeResponse(401, {}, { url: "/account/profile" }))).resolves.toEqual({
      data: "ok",
    });

    expect(post).toHaveBeenCalledWith(expect.stringMatching(/\/api\/v1\/auth\/refresh$/), {
      refresh_token: "refresh-tok",
      username: "u1",
    });
    expect(mockSaveSession).toHaveBeenCalledWith(
      expect.objectContaining({
        accessToken: "new-access",
        user: expect.objectContaining({ avatarUrl: "https://x/a.png" }),
      }),
    );
    expect(retry).toHaveBeenCalledWith(expect.objectContaining({ _retriedAfterRefresh: true }));
    expect(mockClearSession).not.toHaveBeenCalled();
  });

  it("signs out when the refresh is rejected", async () => {
    vi.spyOn(axios, "post").mockRejectedValue(makeResponse(401));
    const retry = vi.spyOn(apiClient, "request");

    await expect(reject(makeResponse(401, {}, { url: "/account/profile" }))).rejects.toBeDefined();

    expect(retry).not.toHaveBeenCalled();
    expect(mockClearSession).toHaveBeenCalledOnce();
    expect(window.location.href).toContain("/sign-in?next=");
  });

  it("does not refresh a session saved before Cognito (no username)", async () => {
    mockReadSession.mockReturnValue({ ...session, user: { id: "u1", email: "a@b.com" } });
    const post = vi.spyOn(axios, "post");

    await expect(reject(makeResponse(401, {}, { url: "/account/profile" }))).rejects.toBeDefined();

    expect(post).not.toHaveBeenCalled();
    expect(mockClearSession).toHaveBeenCalledOnce();
  });

  it("hands a bad-credentials 401 from /auth/* back to the form untouched", async () => {
    const post = vi.spyOn(axios, "post");
    const err = makeResponse(401, {}, { url: "/auth/sign-in" });

    await expect(reject(err)).rejects.toBe(err);

    // No refresh, no sign-out, no reload: the form must keep showing its error.
    expect(post).not.toHaveBeenCalled();
    expect(mockClearSession).not.toHaveBeenCalled();
    expect(window.location.href).toBe("");
  });

  it("does not refresh twice for the same request", async () => {
    const post = vi.spyOn(axios, "post");

    await expect(
      reject(makeResponse(401, {}, { url: "/account/profile", _retriedAfterRefresh: true })),
    ).rejects.toBeDefined();

    expect(post).not.toHaveBeenCalled();
    expect(mockClearSession).toHaveBeenCalledOnce();
  });

  it("shares one refresh call between concurrent 401s", async () => {
    const post = vi.spyOn(axios, "post").mockResolvedValue({ data: refreshed });
    vi.spyOn(apiClient, "request").mockResolvedValue({ data: "ok" });

    await Promise.all([
      reject(makeResponse(401, {}, { url: "/account/profile" })),
      reject(makeResponse(401, {}, { url: "/account/saved" })),
    ]);

    expect(post).toHaveBeenCalledOnce();
  });
});
