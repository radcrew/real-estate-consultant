import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import { BACKEND_BASE_URL, OAUTH_CALLBACK_PATH } from "@config/env";
import { toStoredSession } from "@lib/auth-session";
import { OAUTH_STATE_COOKIE, type OAuthState, safeNextPath } from "@lib/cognito-hosted-ui";
import type { SignInResponse } from "@services/auth";

const APP_SESSION_COOKIE = "radestate.session";
const ONE_WEEK_SECONDS = 60 * 60 * 24 * 7;

/** Why the callback bailed. Echoed to the URL so a failure can be reported
 *  from the address bar without digging through function logs. */
type FailureReason =
  | "missing_code"
  | "provider_error"
  | "state_mismatch"
  | "exchange_failed"
  | "unexpected";

const buildSignInErrorUrl = (origin: string, message: string, reason: FailureReason) => {
  const url = new URL("/sign-in", origin);
  url.searchParams.set("oauth_error", message);
  url.searchParams.set("oauth_reason", reason);
  return url;
};

const clearStateCookie = (response: NextResponse) => {
  response.cookies.set(OAUTH_STATE_COOKIE, "", { path: OAUTH_CALLBACK_PATH, maxAge: 0 });
};

const failSignIn = (origin: string, reason: FailureReason, detail?: string) => {
  console.error(`[oauth] callback failed (${reason})${detail ? `: ${detail}` : ""}`);
  const message =
    reason === "missing_code"
      ? "Missing OAuth code. Try signing in again."
      : "Sign-in failed. Please try again.";
  const response = NextResponse.redirect(buildSignInErrorUrl(origin, message, reason));
  clearStateCookie(response);
  return response;
};

const readState = async (): Promise<OAuthState | null> => {
  const raw = (await cookies()).get(OAUTH_STATE_COOKIE)?.value;
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as OAuthState;
  } catch {
    return null;
  }
};

/**
 * Cognito redirects here after Google sign-in. Check the state, then let the backend
 * trade the code for tokens: it holds the client secret and syncs the profile.
 */
export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const { searchParams, origin } = requestUrl;

  // e.g. the user cancelled at Google: Cognito sends error/error_description, no code.
  const providerError = searchParams.get("error");
  if (providerError) {
    return failSignIn(origin, "provider_error", searchParams.get("error_description") ?? providerError);
  }

  const code = searchParams.get("code");
  if (!code) {
    return failSignIn(origin, "missing_code");
  }

  const saved = await readState();
  if (!saved || saved.state !== searchParams.get("state")) {
    return failSignIn(origin, "state_mismatch");
  }

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/api/v1/auth/oauth/exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, redirect_uri: `${origin}${OAUTH_CALLBACK_PATH}` }),
      cache: "no-store",
    });
    if (!res.ok) {
      return failSignIn(origin, "exchange_failed", `${res.status} ${await res.text()}`);
    }

    const session = toStoredSession((await res.json()) as SignInResponse);
    const response = NextResponse.redirect(new URL(safeNextPath(saved.next), origin));
    // Plain JSON: Next URL-encodes cookie values itself, and readSessionFromCookie decodes
    // once. Encoding here as well left the browser a value it could not parse.
    response.cookies.set(APP_SESSION_COOKIE, JSON.stringify(session), {
      path: "/",
      maxAge: ONE_WEEK_SECONDS,
      sameSite: "lax",
    });
    clearStateCookie(response);
    return response;
  } catch (err) {
    return failSignIn(origin, "unexpected", err instanceof Error ? err.message : String(err));
  }
}
