import { NextResponse } from "next/server";

import { COGNITO_LOGOUT_DONE_PATH, COGNITO_LOGOUT_PATH } from "@config/env";
import {
  AFTER_LOGOUT_COOKIE,
  buildLogoutUrl,
  safeNextPath,
} from "@lib/cognito-hosted-ui";

// Long enough for the round trip through Cognito's /logout.
const AFTER_LOGOUT_MAX_AGE_SECONDS = 300;

/**
 * Send the browser through Cognito's /logout to drop its Hosted UI session, then on to
 * `?next=` (a same-site path) or home. Cognito returns to the fixed done route, so `next`
 * waits in a short-lived cookie.
 */
export function GET(request: Request) {
  const { origin, searchParams } = new URL(request.url);
  const next = safeNextPath(searchParams.get("next"));

  const logoutUrl = buildLogoutUrl(`${origin}${COGNITO_LOGOUT_DONE_PATH}`);
  if (!logoutUrl) {
    return NextResponse.redirect(new URL(next, origin));
  }

  const response = NextResponse.redirect(logoutUrl);
  response.cookies.set(AFTER_LOGOUT_COOKIE, next, {
    path: COGNITO_LOGOUT_PATH,
    maxAge: AFTER_LOGOUT_MAX_AGE_SECONDS,
    httpOnly: true,
    sameSite: "lax",
  });
  return response;
}
