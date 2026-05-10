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

export const getApiErrorMessage = (error: unknown): string => {
  if (!isAxiosError(error)) {
    return "Request failed.";
  }

  const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
  const fromDetail = detailFromPayload(detail);
  if (fromDetail) {
    return fromDetail;
  }

  return "Request failed.";
};
