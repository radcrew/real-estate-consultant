/** One cookie's decoded value from a request's Cookie header, or null if absent or malformed. */
export const getRequestCookie = (request: Request, name: string): string | null => {
  const prefix = `${name}=`;
  const raw = request.headers
    .get("cookie")
    ?.split(/;\s*/)
    .find((part) => part.startsWith(prefix))
    ?.slice(prefix.length);
  if (!raw) {
    return null;
  }
  try {
    return decodeURIComponent(raw);
  } catch {
    return null;
  }
};
