"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { Button } from "@components/ui/button";

import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { GoogleAuthButton } from "../google-auth-button";
import { useSignIn } from "../hooks/use-sign-in";

export const SignInForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSuccess = useCallback(() => {
    router.push("/");
    router.refresh();
  }, [router]);

  const { signIn, error, isSigningIn } = useSignIn(handleSuccess);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await signIn({ email, password });
  };

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">
        {error && (
          <p role="alert" className="mb-4 text-sm text-destructive">
            {error}
          </p>
        )}

        <div className="flex flex-col gap-5">
          <EmailField
            id="sign-in-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSigningIn}
          />
          <PasswordField
            id="sign-in-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            disabled={isSigningIn}
          />
        </div>

        <Button type="submit" disabled={isSigningIn} className="mt-6 w-full">
          {isSigningIn ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-card px-2 text-muted-foreground">or</span>
        </div>
      </div>

      <GoogleAuthButton formPending={isSigningIn} />
    </div>
  );
};
