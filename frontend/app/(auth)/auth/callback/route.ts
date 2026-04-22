import { NextResponse } from "next/server";

import type { StoredSession } from "@lib/auth-session";
import { getSupabaseServerClient } from "@lib/supabase-server";

const APP_SESSION_COOKIE = "radestate.session";
const ONE_WEEK_SECONDS = 60 * 60 * 24 * 7;

const buildSignInErrorUrl = (origin: string, message: string) => {
  const url = new URL("/sign-in", origin);
  url.searchParams.set("oauth_error", message);
  return url;
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
    return NextResponse.redirect(
      buildSignInErrorUrl(requestUrl.origin, "Missing OAuth code. Try signing in again."),
    );
  }

  try {
    const supabase = await getSupabaseServerClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);

    if (error || !data.session?.refresh_token) {
      const message = error?.message || "No session returned. Try signing in again.";
      return NextResponse.redirect(buildSignInErrorUrl(requestUrl.origin, message));
    }

    const session: StoredSession = {
      accessToken: data.session.access_token,
      refreshToken: data.session.refresh_token,
      expiresIn: data.session.expires_in ?? 3600,
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
    const message = err instanceof Error ? err.message : "Sign-in failed.";
    return NextResponse.redirect(buildSignInErrorUrl(requestUrl.origin, message));
  }
}
