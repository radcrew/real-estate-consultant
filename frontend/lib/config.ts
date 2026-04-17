/**
 * Server-side configuration (Route Handlers, Server Components, Server Actions).
 * Do not import from client components if this file grows to include secrets.
 */

/** Base URL of the FastAPI backend (proxy targets; browser does not call it directly). */
export const BACKEND_BASE_URL = process.env.BACKEND_API_URL?.trim() || "http://localhost:8000";
