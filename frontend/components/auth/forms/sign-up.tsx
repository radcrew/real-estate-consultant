"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useCallback, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { AuthFormDivider } from "./divider";
import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { TextField } from "../fields/text";
import { GoogleAuthButton } from "./button";

export const SignUpForm = () => {
  const router = useRouter();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
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

    const fn = firstName.trim();
    const ln = lastName.trim();
    if (!fn || !ln) {
      setValidationError("First name and last name are required.");
      return;
    }

    await signUp({ email, password, firstName: fn, lastName: ln }, handleSuccess);
  };

  return (
    <div className="flex flex-col gap-5">
      <form onSubmit={handleSubmit} className="flex flex-col">
        <AuthFormError message={validationError ?? requestError} />

        <div className="flex flex-col gap-5">
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
            <TextField
              id="sign-up-firstName"
              label="First name"
              name="firstName"
              autoComplete="given-name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              disabled={isSubmitting}
            />
            <TextField
              id="sign-up-lastName"
              label="Last name"
              name="lastName"
              autoComplete="family-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
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

        <ButtonPrimary type="submit" disabled={isSubmitting} className="mt-6 w-full">
          {isSubmitting ? "Creating account…" : "Create account"}
        </ButtonPrimary>
      </form>

      <AuthFormDivider />

      <GoogleAuthButton label="Sign up with Google" />
    </div>
  );
};
