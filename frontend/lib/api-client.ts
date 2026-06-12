import axios from "axios";

import { clearSession, readSession } from "@lib/auth-session";
import { BACKEND_BASE_URL } from "@lib/config";

export const apiClient = axios.create({
  baseURL: `${BACKEND_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

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
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearSession();
      if (typeof window !== "undefined") {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/sign-in?next=${next}`;
      }
    }
    return Promise.reject(error);
  },
);
