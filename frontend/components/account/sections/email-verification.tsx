"use client";

import { Button } from "@components/ui/button-variants";

import { AccountField } from "../field";
import { ACCOUNT_SECTION_CARD_CLASS } from "../styles";

export type AccountEmailVerificationProps = {
  email: string;
  code: string;
  error: string | null;
  info: string | null;
  submitting: boolean;
  onChangeCode: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onResend: () => void;
};

/** Second step of an email change: the profile keeps the old email until this succeeds. */
export const AccountEmailVerification = ({
  email,
  code,
  error,
  info,
  submitting,
  onChangeCode,
  onSubmit,
  onResend,
}: AccountEmailVerificationProps) => (
  <section className={ACCOUNT_SECTION_CARD_CLASS} aria-label="Confirm new email">
    <form onSubmit={onSubmit} className="flex flex-col gap-5">
      <p role="status" className="text-sm text-muted-foreground">
        {info ?? `We sent a code to ${email}. Enter it to finish changing your email.`}
      </p>
      <AccountField
        id="account-email-code"
        label="Verification code"
        autoComplete="one-time-code"
        value={code}
        onChange={onChangeCode}
        error={error}
        disabled={submitting}
      />
      <div className="flex items-center gap-4 pt-1">
        <Button type="submit" disabled={submitting || !code.trim()}>
          {submitting ? "Verifying…" : "Verify email"}
        </Button>
        <button
          type="button"
          onClick={onResend}
          disabled={submitting}
          className="text-sm font-medium text-primary-600 underline-offset-4 hover:underline disabled:opacity-50"
        >
          Resend code
        </button>
      </div>
    </form>
  </section>
);
