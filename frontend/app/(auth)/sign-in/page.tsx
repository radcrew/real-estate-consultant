import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthPageFooter } from "@components/auth/main/footer";
import { AuthPageTitle } from "@components/auth/main/title";
import { SignInForm } from "@components/auth/forms/sign-in";
import { OAuthErrorNotice } from "@components/auth/notice/oauth-error";
import { SignUpNotice } from "@components/auth/notice/sign-up";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to your RadEstate account",
};

const SignInPage = () => (
  <div className="flex flex-col gap-6">
    <AuthPageTitle
      title="Sign in"
      description="Sign in with Google or the email and password for your RadEstate account."
    />

    <Suspense fallback={null}>
      <OAuthErrorNotice />
      <SignUpNotice />
    </Suspense>

    <SignInForm />

    <AuthPageFooter prompt="No account?" linkHref="/sign-up" linkLabel="Create one" />
  </div>
);

export default SignInPage;
