import { NextResponse } from "next/server";

import { COGNITO_LOGOUT_PATH } from "@config/env";
import { AFTER_LOGOUT_COOKIE, safeNextPath } from "@lib/cognito-hosted-ui";
import { getRequestCookie } from "@utils/common/cookies";

/** Cognito's /logout lands here; continue to the path saved before it, else home. */
export function GET(request: Request) {
  const { origin } = new URL(request.url);
  const next = safeNextPath(getRequestCookie(request, AFTER_LOGOUT_COOKIE));
  const response = NextResponse.redirect(new URL(next, origin));
  response.cookies.set(AFTER_LOGOUT_COOKIE, "", { path: COGNITO_LOGOUT_PATH, maxAge: 0 });
  return response;
}
