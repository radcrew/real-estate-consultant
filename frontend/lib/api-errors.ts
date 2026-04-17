export const parseErrorPayload = async (res: Response): Promise<string> => {
  try {
    const data = (await res.json()) as { detail?: string };
    if (typeof data.detail === "string" && data.detail.trim()) {
      return data.detail.trim();
    }
  } catch {

  }
  return res.statusText || "Request failed.";
};
