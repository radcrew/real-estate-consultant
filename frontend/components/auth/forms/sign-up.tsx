"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { Button } from "@components/ui/button";
import { useAuth } from "@contexts/auth";

import { AuthFormError } from "../auth-form-error";
import { AuthFormDivider } from "../auth-form-divider";
import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { GoogleAuthButton } from "../google-auth-button";

export const SignUpForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const { signUp, error: requestError, isSubmitting } = useAuth();

  const handleSuccess = useCallback(() => {
    router.push("/sign-in?registered=1");
    router.refresh();
  }, [router]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setValidationError(null);

    if (password !== confirmPassword) {
      setValidationError("Passwords do not match.");
      return;
    }

    await signUp({ email, password }, handleSuccess);
  };

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">
        <AuthFormError message={validationError ?? requestError} />

        <div className="flex flex-col gap-5">
          <EmailField
            id="sign-up-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
          />
          <PasswordField
            id="sign-up-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            disabled={isSubmitting}
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
            disabled={isSubmitting}
          />
        </div>

        <Button type="submit" disabled={isSubmitting} className="mt-6 w-full">
          {isSubmitting ? "Creating account…" : "Create account"}
        </Button>
      </form>

      <AuthFormDivider />

      <GoogleAuthButton label="Sign up with Google" />
    </div>
  );
};
