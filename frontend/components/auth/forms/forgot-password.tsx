"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";

import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { EmailField } from "../fields/email";

export const ForgotPasswordForm = () => {
  const router = useRouter();
  const [email, setEmail] = useState("");

  const { requestPasswordReset, error, isSubmitting } = useAuth();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await requestPasswordReset(email, () =>
      router.push(`/reset-password?email=${encodeURIComponent(email.trim())}`),
    );
  };

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
        {isSubmitting ? "Sending…" : "Send reset code"}
      </ButtonPrimary>
    </form>
  );
};
