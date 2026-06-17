"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useRef, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { getSupabaseBrowserClient } from "@lib/supabase-browser";

import { useAuth } from "@contexts/auth";

import { AuthFormError } from "./error";
import { PasswordField } from "../fields/password";

type LinkState = "verifying" | "ready" | "invalid";

export const ResetPasswordForm = () => {
  const searchParams = useSearchParams();
  const [linkState, setLinkState] = useState<LinkState>("verifying");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);
  const [done, setDone] = useState(false);
  const exchangeStartedRef = useRef(false);

  const { updatePassword, error, isSubmitting, clearError } = useAuth();

  // Establish a session from the recovery link (PKCE `code`) before allowing a
  // password change. A valid Supabase session is required for updateUser().
  useEffect(() => {
    if (exchangeStartedRef.current) return;
    exchangeStartedRef.current = true;

    const code = searchParams.get("code");
    const supabase = getSupabaseBrowserClient();

    void (async () => {
      // Already signed in from the recovery link (e.g. returning to this tab).
      const { data: existing } = await supabase.auth.getSession();
      if (existing.session) {
        setLinkState("ready");
        return;
      }

      if (!code) {
        setLinkState("invalid");
        return;
      }

      const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code);
      setLinkState(exchangeError ? "invalid" : "ready");
    })();
  }, [searchParams]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearError();

    if (password !== confirm) {
      setMismatch(true);
      return;
    }
    setMismatch(false);

    await updatePassword(password, () => setDone(true));
  };

  if (done) {
    return (
      <div className="flex flex-col gap-5">
        <p
          role="status"
          className="rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3 text-sm text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200"
        >
          Your password has been updated. You can now sign in with your new password.
        </p>
        <ButtonPrimary href="/sign-in" className="w-full">
          Go to sign in
        </ButtonPrimary>
      </div>
    );
  }

  if (linkState === "verifying") {
    return (
      <p className="text-center text-sm text-muted-foreground" role="status">
        Verifying your reset link…
      </p>
    );
  }

  if (linkState === "invalid") {
    return (
      <div className="flex flex-col gap-5">
        <p role="alert" className="text-sm text-destructive">
          This password reset link is invalid or has expired. Please request a new one.
        </p>
        <Link
          href="/forgot-password"
          className="text-center text-sm font-semibold text-primary-600 underline-offset-4 hover:underline"
        >
          Request a new reset link
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col">
      <AuthFormError message={error ?? (mismatch ? "Passwords do not match." : null)} />

      <div className="flex flex-col gap-5">
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
    </form>
  );
};
