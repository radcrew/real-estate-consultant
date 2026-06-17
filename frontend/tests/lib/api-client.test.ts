// @vitest-environment jsdom
import axios from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock auth-session before importing api-client so the interceptors pick up the mock
vi.mock("@lib/auth-session", () => ({
  readSession: vi.fn(),
  clearSession: vi.fn(),
}));

import { readSession, clearSession } from "@lib/auth-session";
import { apiClient } from "@lib/api-client";

const mockReadSession = vi.mocked(readSession);
const mockClearSession = vi.mocked(clearSession);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const makeResponse = (status: number, data: unknown = {}) =>
  new axios.AxiosError("Request failed", String(status), undefined, undefined, {
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
