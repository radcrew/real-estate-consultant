import type { Metadata } from "next";
import Link from "next/link";

import { SignUpForm } from "@/components/auth/forms/sign-up";

export const metadata: Metadata = {
  title: "Create account",
  description: "Create a RadEstate account",
};

const SignUpPage = () => (
  <div className="flex flex-col gap-6">
    <div>
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Create account
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Sign up with your work email. You can sign in on the next screen.
      </p>
    </div>
    <SignUpForm />
    <p className="text-center text-sm text-muted-foreground">
      Already have an account?{" "}
      <Link
        href="/sign-in"
        className="font-semibold text-primary underline-offset-4 hover:underline"
      >
        Sign in
      </Link>
    </p>
  </div>
);

export default SignUpPage;
