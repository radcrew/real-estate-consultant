/**
 * Cognito Hosted UI, used only for Google sign-in. Server-side only: read from route
 * handlers, never shipped to the browser (so no NEXT_PUBLIC_ prefix). The client secret
 * stays on the backend, which does the code exchange.
 */

export const OAUTH_STATE_COOKIE = "radestate.oauth_state";
export const OAUTH_STATE_MAX_AGE_SECONDS = 300;

// Holds the `next` path across Cognito's /logout, whose return URL must be a fixed,
// allow-listed address and so cannot carry it.
export const AFTER_LOGOUT_COOKIE = "radestate.after_logout";

// Must be a subset of the app client's allowed OpenID Connect scopes, or Cognito rejects
// the whole request (invalid_scope). aws.cognito.signin.user.admin is left out until the
// client allows it: without it, sign-out cannot revoke a Google user's tokens server-side
// (/auth/sign-out treats that refusal as signed out) and they simply expire.
const SCOPES = "openid email profile";

export type OAuthState = {
  state: string;
  next: string;
  // Set on the second pass after the backend linked Google to an existing account.
  relink?: boolean;
};

// Backend 409 detail: Google was just linked to an existing account; sign in once more.
export const OAUTH_ACCOUNT_LINKED = "account_linked";

/** Keep only same-origin relative paths, so `next` cannot send users off-site. */
export const safeNextPath = (next: string | null): string =>
  next && next.startsWith("/") && !next.startsWith("//") ? next : "/";

/**
 * `forceLogin` adds prompt=login, which makes Cognito ignore its own hosted-login session.
 * The retry after account linking needs it: that session still belongs to the google_
 * user that linking deleted, and reusing it yields a code Cognito then refuses
 * (invalid_grant). Cognito forwards the prompt to Google, so it is not used by default.
 */
export const buildGoogleAuthorizeUrl = (
  redirectUri: string,
  state: string,
  { forceLogin = false }: { forceLogin?: boolean } = {},
): URL | null => {
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
  if (forceLogin) {
    url.searchParams.set("prompt", "login");
  }
  return url;
};

/**
 * Cognito's /logout deletes the Hosted UI session cookie it keeps on its own domain (our
 * app cannot touch that cookie), then redirects to `logoutUri`. The URI must be listed
 * in the app client's allowed sign-out URLs.
 */
export const buildLogoutUrl = (logoutUri: string): URL | null => {
  const domain = process.env.COGNITO_DOMAIN?.trim().replace(/\/+$/, "");
  const clientId = process.env.COGNITO_CLIENT_ID?.trim();
  if (!domain || !clientId) {
    return null;
  }

  const url = new URL(`${domain}/logout`);
  url.searchParams.set("client_id", clientId);
  url.searchParams.set("logout_uri", logoutUri);
  return url;
};
