import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthPageFooter } from "@components/auth/main/footer";
import { AuthPageTitle } from "@components/auth/main/title";
import { ForgotPasswordForm } from "@components/auth/forms/forgot-password";

export const metadata: Metadata = {
  title: "Forgot password",
  description: "Reset the password for your RadEstate account.",
};

const ForgotPasswordPage = () => (
  <div className="flex flex-col gap-6">
    <AuthPageTitle
      title="Forgot password?"
      description="Enter the email for your account and we'll send you a link to reset your password."
    />

    <Suspense fallback={null}>
      <ForgotPasswordForm />
    </Suspense>

    <AuthPageFooter prompt="Remembered it?" linkHref="/sign-in" linkLabel="Back to sign in" />
  </div>
);

export default ForgotPasswordPage;
