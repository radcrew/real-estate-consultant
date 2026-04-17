import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { SignUpNotice } from "@/components/auth/sign-up-notice";
import { SignInForm } from "@/components/auth/forms/sign-in";

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
        Use the email and password for your RadEstate account.
      </p>
    </div>
    <Suspense fallback={null}>
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
