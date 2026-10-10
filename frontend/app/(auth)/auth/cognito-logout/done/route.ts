import { NextResponse } from "next/server";

import { COGNITO_LOGOUT_PATH } from "@config/env";
import { AFTER_LOGOUT_COOKIE, safeNextPath } from "@lib/cognito-hosted-ui";

const readAfterLogout = (request: Request): string | null => {
  const prefix = `${AFTER_LOGOUT_COOKIE}=`;
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

/** Cognito's /logout lands here; continue to the path saved before it, else home. */
export function GET(request: Request) {
  const { origin } = new URL(request.url);
  const next = safeNextPath(readAfterLogout(request));
  const response = NextResponse.redirect(new URL(next, origin));
  response.cookies.set(AFTER_LOGOUT_COOKIE, "", { path: COGNITO_LOGOUT_PATH, maxAge: 0 });
  return response;
}
