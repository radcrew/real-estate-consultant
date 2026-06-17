import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthPageFooter } from "@components/auth/main/footer";
import { AuthPageTitle } from "@components/auth/main/title";
import { ResetPasswordForm } from "@components/auth/forms/reset-password";

export const metadata: Metadata = {
  title: "Reset password",
  description: "Set a new password for your RadEstate account.",
};

const ResetPasswordPage = () => (
  <div className="flex flex-col gap-6">
    <AuthPageTitle
      title="Set a new password"
      description="Choose a new password for your RadEstate account."
    />

    <Suspense fallback={null}>
      <ResetPasswordForm />
    </Suspense>

    <AuthPageFooter prompt="Remembered it?" linkHref="/sign-in" linkLabel="Back to sign in" />
  </div>
);

export default ResetPasswordPage;
