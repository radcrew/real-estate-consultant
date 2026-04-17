import type { Metadata } from "next";
import Link from "next/link";

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
        Welcome back. Account form and server integration will be added in a
        later step.
      </p>
    </div>
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
