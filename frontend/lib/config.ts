/**
 * Server-side base URL (Next route handlers, Server Actions, etc.).
 * Not exposed to the browser unless prefixed with `NEXT_PUBLIC_`.
 */
export const BACKEND_BASE_URL =
  process.env.BACKEND_API_URL?.trim() || "http://localhost:8000";

/**
 * Base URL of the FastAPI backend for code that runs in the browser.
 * Set `NEXT_PUBLIC_BACKEND_API_URL` in `.env` (defaults match local dev).
 */
export const PUBLIC_BACKEND_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_API_URL?.trim() || "http://localhost:8000";
