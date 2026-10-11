"use client";

import { useSearchParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";

import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { EmailField } from "../fields/email";
import { PasswordField } from "../fields/password";
import { TextField } from "../fields/text";

const NOTICE_CLASS =
  "rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200";

export const ResetPasswordForm = () => {
  // Forgot-password sends the user here as ?email=<address>.
  const initialEmail = useSearchParams().get("email") ?? "";
  const [email, setEmail] = useState(initialEmail);
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const [info, setInfo] = useState(
    initialEmail
      ? `If an account exists for ${initialEmail}, we've sent it a reset code. Check your inbox and spam folder.`
      : "",
  );
  const [done, setDone] = useState(false);

  const { requestPasswordReset, resetPassword, error, isSubmitting, clearError } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearError();
    setInfo("");

    if (password !== confirm) {
      setMismatch(true);
      return;
    }
    setMismatch(false);

    await resetPassword({ email, code, password }, () => setDone(true));
  };

  const handleResend = async () => {
    setInfo("");
    await requestPasswordReset(email, () =>
      setInfo(`If an account exists for ${email.trim()}, we've sent it a new code.`),
    );
  };

  if (done) {
    return (
      <div className="flex flex-col gap-5">
        <p role="status" className={NOTICE_CLASS}>
          Your password has been updated. You can now sign in with your new password.
        </p>
        <ButtonPrimary href="/sign-in" className="w-full">
          Go to sign in
        </ButtonPrimary>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col">
      <AuthFormError message={error ?? (mismatch ? "Passwords do not match." : null)} />
      {info && (
        <p role="status" className={`mb-5 ${NOTICE_CLASS}`}>
          {info}
        </p>
      )}

      <div className="flex flex-col gap-5">
        <EmailField
          id="reset-email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={isSubmitting}
        />
        <TextField
          id="reset-code"
          label="Reset code"
          name="code"
          autoComplete="one-time-code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          disabled={isSubmitting}
        />
        <PasswordField
          id="reset-password"
          label="New password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={isSubmitting}
        />
        <PasswordField
          id="reset-password-confirm"
          label="Confirm new password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          disabled={isSubmitting}
        />
      </div>

      <ButtonPrimary type="submit" disabled={isSubmitting} className="mt-6 w-full">
        {isSubmitting ? "Updating…" : "Update password"}
      </ButtonPrimary>
      <button
        type="button"
        onClick={handleResend}
        disabled={isSubmitting || !email.trim()}
        className="mt-3 text-sm font-medium text-primary-600 underline-offset-4 hover:underline disabled:opacity-50"
      >
        Send a new code
      </button>
    </form>
  );
};
