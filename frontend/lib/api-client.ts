import axios from "axios";

import { BACKEND_BASE_URL } from "@lib/config";

/** Axios instance for FastAPI `/api/v1` (browser and server). */
export const apiClient = axios.create({
  baseURL: `${BACKEND_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});
