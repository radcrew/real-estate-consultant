"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { TextField } from "../fields/text";

type VerifyEmailFormProps = {
  email: string;
  // Set when the user just signed up in this tab; lets us sign them in right after.
  password?: string;
};

export const VerifyEmailForm = ({ email, password }: VerifyEmailFormProps) => {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [info, setInfo] = useState(`We sent a verification code to ${email}.`);

  const { confirmSignUp, resendCode, signIn, error, isSubmitting } = useAuth();

  const handleVerified = async () => {
    if (!password) {
      router.push("/sign-in?registered=1");
      return;
    }
    await signIn({ email, password }, () => {
      router.push("/");
      router.refresh();
    });
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
