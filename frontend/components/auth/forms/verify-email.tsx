"use client";

import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { COGNITO_LOGOUT_PATH } from "@config/env";
import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { TextField } from "../fields/text";

type VerifyEmailFormProps = {
  email: string;
  // Set when the user just signed up in this tab; lets us sign them in right after.
  password?: string;
  // Same-site path to land on once verified (the sign-in page's `next`).
  next?: string | null;
};

export const VerifyEmailForm = ({ email, password, next }: VerifyEmailFormProps) => {
  const [code, setCode] = useState("");
  const [info, setInfo] = useState(`We sent a verification code to ${email}.`);

  const { confirmSignUp, resendCode, signIn, error, isSubmitting } = useAuth();

  // After sign-up, pass through Cognito's sign-out so no Hosted UI session from an
  // earlier Google sign-in survives: the sign-up merge may have deleted that user, and a
  // session for a deleted user makes the next "Continue with Google" fail.
  const handleVerified = async () => {
    const logout = next
      ? `${COGNITO_LOGOUT_PATH}?next=${encodeURIComponent(next)}`
      : COGNITO_LOGOUT_PATH;
    if (!password) {
      window.location.assign(logout);
      return;
    }
    await signIn({ email, password }, () => window.location.assign(logout));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setInfo("");
    await confirmSignUp(email, code, handleVerified);
  };

  const handleResend = async () => {
    setInfo("");
    await resendCode(email, () => setInfo(`We sent a new code to ${email}.`));
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col">
      <AuthFormError message={error} />
      {info && (
        <p role="status" className="mb-5 text-sm text-muted-foreground">
          {info}
        </p>
      )}

      <TextField
        id="verify-email-code"
        label="Verification code"
        name="code"
        autoComplete="one-time-code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        disabled={isSubmitting}
      />

      <ButtonPrimary type="submit" disabled={isSubmitting} className="mt-6 w-full">
        {isSubmitting ? "Verifying…" : "Verify email"}
      </ButtonPrimary>
      <button
        type="button"
        onClick={handleResend}
        disabled={isSubmitting}
        className="mt-3 text-sm font-medium text-primary-600 underline-offset-4 hover:underline disabled:opacity-50"
      >
        Resend code
      </button>
    </form>
  );
};
