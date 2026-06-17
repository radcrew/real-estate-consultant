import { isAxiosError } from "axios";

type FastApiValidationItem = { msg?: string };

const detailFromPayload = (detail: unknown): string | null => {
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as FastApiValidationItem).msg ?? "").trim();
        }
        return "";
      })
      .filter(Boolean);
    if (parts.length) {
      return parts.join(" ");
    }
  }
  return null;
};

/** User-friendly fallback message for an HTTP status when the body has no detail. */
const messageForStatus = (status: number): string => {
  if (status === 400) return "Something looks off with that request. Please review your answers and try again.";
  if (status === 401) return "Your session has expired. Please sign in and try again.";
  if (status === 403) return "You don't have permission to do that.";
  if (status === 404) return "We couldn't find what you were looking for. It may have been moved or removed.";
  if (status === 409) return "That action conflicts with the current state. Please refresh and try again.";
  if (status === 429) return "You're going a bit fast — please wait a moment and try again.";
  if (status >= 500) return "Our server ran into a problem. Please try again in a few moments.";
  return "Something went wrong. Please try again.";
};

export const getApiErrorMessage = (error: unknown): string => {
  if (!isAxiosError(error)) {
    return "Something went wrong. Please try again.";
  }

  // Request was made but no response arrived (network down, CORS, server unreachable).
  if (!error.response) {
    if (error.code === "ECONNABORTED" || error.message?.toLowerCase().includes("timeout")) {
      return "The request timed out. Please check your connection and try again.";
    }
    return "We couldn't reach the server. Please check your internet connection and try again.";
  }

  // Prefer a specific message from the API payload when present.
  const detail = (error.response.data as { detail?: unknown } | undefined)?.detail;
  const fromDetail = detailFromPayload(detail);
  if (fromDetail) {
    return fromDetail;
  }

  return messageForStatus(error.response.status);
};
