/**
 * Cognito Hosted UI, used only for Google sign-in. Server-side only: read from route
 * handlers, never shipped to the browser (so no NEXT_PUBLIC_ prefix). The client secret
 * stays on the backend, which does the code exchange.
 */

export const OAUTH_STATE_COOKIE = "radestate.oauth_state";
export const OAUTH_STATE_MAX_AGE_SECONDS = 300;

// Must be a subset of the app client's allowed OpenID Connect scopes, or Cognito rejects
// the whole request (invalid_scope). aws.cognito.signin.user.admin is left out until the
// client allows it: without it, sign-out cannot revoke a Google user's tokens server-side
// (/auth/sign-out treats that refusal as signed out) and they simply expire.
const SCOPES = "openid email profile";

export type OAuthState = {
  state: string;
  next: string;
};

/** Keep only same-origin relative paths, so `next` cannot send users off-site. */
export const safeNextPath = (next: string | null): string =>
  next && next.startsWith("/") && !next.startsWith("//") ? next : "/";

export const buildGoogleAuthorizeUrl = (redirectUri: string, state: string): URL | null => {
  const domain = process.env.COGNITO_DOMAIN?.trim().replace(/\/+$/, "");
  const clientId = process.env.COGNITO_CLIENT_ID?.trim();
  if (!domain || !clientId) {
    return null;
  }

  const url = new URL(`${domain}/oauth2/authorize`);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("redirect_uri", redirectUri);
  url.searchParams.set("scope", SCOPES);
  url.searchParams.set("state", state);
  url.searchParams.set("identity_provider", "Google");
  return url;
};
