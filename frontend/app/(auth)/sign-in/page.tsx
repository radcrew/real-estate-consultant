import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { SignInForm } from "@components/auth/forms/sign-in";
import { OAuthErrorNotice } from "@components/auth/oauth-error-notice";
import { SignUpNotice } from "@components/auth/sign-up-notice";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to your RadEstate account",
};

const SignInPage = () => (
  <div className="flex flex-col gap-6">
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Sign in
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Sign in with Google or the email and password for your RadEstate account.
      </p>
    </div>
    <Suspense fallback={null}>
      <OAuthErrorNotice />
      <SignUpNotice />
    </Suspense>
    <SignInForm />
    <p className="text-center text-sm text-muted-foreground">
      No account?{" "}
      <Link
        href="/sign-up"
        className="font-semibold text-primary underline-offset-4 hover:underline"
      >
        Create one
      </Link>
    </p>
  </div>
);

export default SignInPage;
