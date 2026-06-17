"use client";

import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";

import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { EmailField } from "../fields/email";

export const ForgotPasswordForm = () => {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const { requestPasswordReset, error, isSubmitting } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await requestPasswordReset(email, () => setSent(true));
  };

  if (sent) {
    return (
      <p
        role="status"
        className="rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200"
      >
        If an account exists for <span className="font-medium">{email.trim()}</span>,
        we&rsquo;ve sent a link to reset your password. Check your inbox and spam folder.
      </p>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col">
      <AuthFormError message={error} />

      <EmailField
        id="forgot-email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={isSubmitting}
      />

      <ButtonPrimary type="submit" disabled={isSubmitting} className="mt-6 w-full">
        {isSubmitting ? "Sending…" : "Send reset link"}
      </ButtonPrimary>
    </form>
  );
};
