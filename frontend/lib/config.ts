/**
 * Base URL of the FastAPI backend for the browser and shared axios client.
 * Set `NEXT_PUBLIC_BACKEND_API_URL` in `.env`.
 */
export const PUBLIC_BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_API_URL?.trim() || "http://localhost:8000";
