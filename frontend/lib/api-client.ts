import axios, { type InternalAxiosRequestConfig } from "axios";

import { clearSession, readSession, saveSession, toStoredSession } from "@lib/auth-session";
import { BACKEND_BASE_URL } from "@config/env";
import type { SignInResponse } from "@services/auth";

const API_BASE_URL = `${BACKEND_BASE_URL}/api/v1`;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

type RetriableConfig = InternalAxiosRequestConfig & { _retriedAfterRefresh?: boolean };

// Concurrent 401s share one refresh call instead of each spending the refresh token.
let refreshInFlight: Promise<boolean> | null = null;

/**
 * Trade the stored refresh token for a new access token. Uses bare axios, not apiClient,
 * so a 401 from /auth/refresh cannot re-enter this interceptor.
 */
const refreshSession = (): Promise<boolean> => {
  refreshInFlight ??= (async () => {
    const session = readSession();
    if (!session?.refreshToken || !session.user.username) {
      return false;
    }
    try {
      const { data } = await axios.post<SignInResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: session.refreshToken,
        username: session.user.username,
      });
      saveSession(toStoredSession(data, session));
      return true;
    } catch {
      return false;
    }
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
};

const redirectToSignIn = (): void => {
  clearSession();
  if (typeof window !== "undefined") {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/sign-in?next=${next}`;
  }
};

apiClient.interceptors.request.use((config) => {
  const session = readSession();

  if (!session?.accessToken) {
    return config;
  }

  config.headers.set("Authorization", `Bearer ${session.accessToken}`);

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    const config = error.config as RetriableConfig | undefined;
    // /auth/* answers 401 for bad credentials, not for an expired session. Hand it back to
    // the form: redirecting would reload the sign-in page and wipe the error message.
    if (config?.url?.startsWith("/auth/")) {
      return Promise.reject(error);
    }

    if (config && !config._retriedAfterRefresh && (await refreshSession())) {
      config._retriedAfterRefresh = true;
      // The request interceptor re-reads the session and sends the new token.
      return apiClient.request(config);
    }

    redirectToSignIn();
    return Promise.reject(error);
  },
);
