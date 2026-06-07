"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";

import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { AuthFormDivider } from "./divider";
import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { GoogleAuthButton } from "./button";

export const SignInForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const { signIn, error, isSubmitting } = useAuth();

  const handleSuccess = useCallback(() => {
    router.push("/");
    router.refresh();
  }, [router]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await signIn({ email, password }, handleSuccess);
  };

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">
        <AuthFormError message={error} />

        <div className="flex flex-col gap-5">
          <EmailField
            id="sign-in-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
          />
          <PasswordField
            id="sign-in-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            disabled={isSubmitting}
          />
        </div>

        <ButtonPrimary type="submit" disabled={isSubmitting} className="mt-6 w-full">
          {isSubmitting ? "Signing in…" : "Sign in"}
        </ButtonPrimary>
      </form>

      <AuthFormDivider />

      <GoogleAuthButton />
    </div>
  );
};
