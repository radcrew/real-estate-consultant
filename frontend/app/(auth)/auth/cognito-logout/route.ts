import { NextResponse } from "next/server";

import { buildLogoutUrl } from "@lib/cognito-hosted-ui";

/** Send the browser through Cognito's /logout to drop its Hosted UI session, then home. */
export function GET(request: Request) {
  const { origin } = new URL(request.url);
  const home = `${origin}/`;
  return NextResponse.redirect(buildLogoutUrl(home) ?? home);
}
