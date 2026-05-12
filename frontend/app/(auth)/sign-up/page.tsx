import type { Metadata } from "next";

import { AuthPageFooter } from "@components/auth/main/footer";
import { AuthPageTitle } from "@components/auth/main/title";
import { SignUpForm } from "@components/auth/forms/sign-up";

export const metadata: Metadata = {
  title: "Create account",
  description: "Create a RadEstate account",
};

const SignUpPage = () => (
  <div className="flex flex-col gap-6">
    <AuthPageTitle
      title="Create account"
      description="Create an account with your work email, then sign in on the next screen."
    />
    <SignUpForm />
    <AuthPageFooter
      prompt="Already have an account?"
      linkHref="/sign-in"
      linkLabel="Sign in"
    />
  </div>
);

export default SignUpPage;
