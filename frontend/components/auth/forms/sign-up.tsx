"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { Button } from "@components/ui/button";

import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { GoogleAuthButton } from "../google-auth-button";
import { useSignUp } from "../hooks/use-sign-up";

export const SignUpForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSuccess = useCallback(() => {
    router.push("/sign-in?registered=1");
    router.refresh();
  }, [router]);

  const { signUp, error: requestError, isSigningUp } = useSignUp(handleSuccess);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setValidationError(null);

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    await signUp({ email, password });
  };

  const displayError = validationError ?? requestError;

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">
        {displayError && (
          <p role="alert" className="mb-4 text-sm text-destructive">
            {displayError}
          </p>
        )}

        <div className="flex flex-col gap-5">
          <EmailField
            id="sign-up-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSigningUp}
          />
          <PasswordField
            id="sign-up-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            disabled={isSigningUp}
          >
            <p className="text-xs leading-snug text-muted-foreground">
              Use at least 8 characters (max 72).
            </p>
          </PasswordField>
          <PasswordField
            id="sign-up-confirm"
            label="Confirm password"
            name="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            disabled={isSigningUp}
          />
        </div>

        <Button type="submit" disabled={isSigningUp} className="mt-6 w-full">
          {isSigningUp ? "Creating account…" : "Create account"}
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

      <GoogleAuthButton isFormSubmitting={isSigningUp} label="Sign up with Google" />
    </div>
  );
};
