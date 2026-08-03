import { NextResponse } from "next/server";
import { cookies } from "next/headers";

import type { StoredSession } from "@lib/auth-session";
import { syncProfileNamesAfterOAuth } from "@lib/oauth-profile-sync";
import { getSupabaseServerClient } from "@lib/supabase-server";

const APP_SESSION_COOKIE = "radestate.session";
const ONE_WEEK_SECONDS = 60 * 60 * 24 * 7;

/**
 * Everything `@supabase/ssr` writes is prefixed `sb-<project-ref>-`: the PKCE
 * `-code-verifier`, the `-auth-token` and its `.0`/`.1` size chunks.
 */
const SUPABASE_COOKIE_PREFIX = "sb-";

/** Why the callback bailed. Echoed to the URL so a failure can be reported
 *  from the address bar without digging through function logs. */
type FailureReason = "missing_code" | "exchange_failed" | "no_refresh_token" | "unexpected";

const buildSignInErrorUrl = (origin: string, message: string, reason: FailureReason) => {
  const url = new URL("/sign-in", origin);
  url.searchParams.set("oauth_error", message);
  url.searchParams.set("oauth_reason", reason);
  return url;
};

/**
 * A failed exchange leaves the PKCE verifier — and any half-written session
 * chunks — behind. The next attempt then starts against state that cannot
 * match its freshly minted code, so clear the slate on the way out and let the
 * retry begin from nothing.
 */
const clearSupabaseAuthCookies = async (response: NextResponse) => {
  const store = await cookies();
  for (const { name } of store.getAll()) {
    if (name.startsWith(SUPABASE_COOKIE_PREFIX)) {
      response.cookies.set(name, "", { path: "/", maxAge: 0 });
    }
  }
};

const failSignIn = async (origin: string, reason: FailureReason, detail?: string) => {
  console.error(`[oauth] callback failed (${reason})${detail ? `: ${detail}` : ""}`);
  const message =
    reason === "missing_code"
      ? "Missing OAuth code. Try signing in again."
      : "Sign-in failed. Please try again.";
  const response = NextResponse.redirect(buildSignInErrorUrl(origin, message, reason));
  await clearSupabaseAuthCookies(response);
  return response;
};

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const requestedNext = requestUrl.searchParams.get("next");
  const nextPath =
    requestedNext && requestedNext.startsWith("/") && !requestedNext.startsWith("//")
      ? requestedNext
      : "/";

  if (!code) {
    return failSignIn(requestUrl.origin, "missing_code");
  }

  try {
    const supabase = await getSupabaseServerClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (error) {
      return failSignIn(requestUrl.origin, "exchange_failed", error.message);
    }

    if (!data.session?.refresh_token) {
      // Previously silent: the exchange reports success but hands back no
      // refresh token, and the user saw the same message as a hard failure.
      return failSignIn(requestUrl.origin, "no_refresh_token");
    }

    await syncProfileNamesAfterOAuth(supabase, data.session.user);

    const session: StoredSession = {
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
      expiresIn: 360000,
      tokenType: data.session.token_type,
      user: {
        id: data.session.user.id,
        email: data.session.user.email ?? null,
      },
    };

    const response = NextResponse.redirect(new URL(nextPath, requestUrl.origin));
    response.cookies.set(APP_SESSION_COOKIE, encodeURIComponent(JSON.stringify(session)), {
      path: "/",
      maxAge: ONE_WEEK_SECONDS,
      sameSite: "lax",
    });
    return response;
  } catch (err) {
    return failSignIn(
      requestUrl.origin,
      "unexpected",
      err instanceof Error ? err.message : String(err),
    );
  }
}
