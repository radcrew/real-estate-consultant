import axios from "axios";

import { readSession } from "@lib/auth-session";
import { BACKEND_BASE_URL } from "@lib/config";

/** Axios instance for FastAPI `/api/v1` (browser and server). */
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
