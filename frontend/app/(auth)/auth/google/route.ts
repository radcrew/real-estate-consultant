import { NextResponse } from "next/server";

import { OAUTH_CALLBACK_PATH } from "@config/env";
import {
  OAUTH_STATE_COOKIE,
  OAUTH_STATE_MAX_AGE_SECONDS,
  type OAuthState,
  buildGoogleAuthorizeUrl,
  safeNextPath,
} from "@lib/cognito-hosted-ui";

/** Start Google sign-in: remember a random state, then hand off to the Cognito Hosted UI. */
export function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const state = crypto.randomUUID();
  const relink = requestUrl.searchParams.get("relink") === "1";
  const authorizeUrl = buildGoogleAuthorizeUrl(
    `${requestUrl.origin}${OAUTH_CALLBACK_PATH}`,
    state,
    { forceLogin: relink },
  );

  if (!authorizeUrl) {
    console.error("[oauth] COGNITO_DOMAIN or COGNITO_CLIENT_ID is not set");
    const signIn = new URL("/sign-in", requestUrl.origin);
    signIn.searchParams.set("oauth_error", "Google sign-in is not available right now.");
    signIn.searchParams.set("oauth_reason", "not_configured");
    return NextResponse.redirect(signIn);
  }

  const payload: OAuthState = {
    state,
    next: safeNextPath(requestUrl.searchParams.get("next")),
    relink,
  };
  const response = NextResponse.redirect(authorizeUrl);
  response.cookies.set(OAUTH_STATE_COOKIE, JSON.stringify(payload), {
    path: OAUTH_CALLBACK_PATH,
    maxAge: OAUTH_STATE_MAX_AGE_SECONDS,
    httpOnly: true,
    sameSite: "lax",
    secure: requestUrl.protocol === "https:",
  });
  return response;
}
