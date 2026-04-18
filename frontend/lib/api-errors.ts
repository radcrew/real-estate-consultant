import { isAxiosError } from "axios";

export const getApiErrorMessage = (error: unknown): string => {
  if (!isAxiosError(error)) {
    return "Request failed.";
  }

  const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail.trim();
  }
  
  return "Request failed.";
};
