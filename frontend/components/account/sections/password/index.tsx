"use client";

import { Button } from "@components/ui/buttons";

import { AccountField } from "../../field";
import { PasswordStrengthMeter } from "../password-meter";
import { ACCOUNT_SECTION_CARD_CLASS } from "../../styles";

export type AccountPasswordSectionProps = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  errors: Partial<Record<string, string>>;
  submitting: boolean;
  success: boolean;
  onChangeCurrent: (value: string) => void;
  onChangeNew: (value: string) => void;
  onChangeConfirm: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
};

export const AccountPasswordSection = ({
  currentPassword,
  newPassword,
  confirmPassword,
  errors,
  submitting,
  success,
  onChangeCurrent,
  onChangeNew,
  onChangeConfirm,
  onSubmit,
}: AccountPasswordSectionProps) => (
  <section className={ACCOUNT_SECTION_CARD_CLASS} aria-labelledby="security-heading">
    <div className="border-b border-border pb-5">
      <h2 id="security-heading" className="text-lg font-semibold text-foreground">
        Security
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Change your password. You must enter your current password.
      </p>
    </div>

    <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5">
      <AccountField
        id="account-current-password"
        label="Current password"
        type="password"
        autoComplete="current-password"
        value={currentPassword}
        onChange={onChangeCurrent}
        error={errors.currentPassword}
      />
      <AccountField
        id="account-new-password"
        label="New password"
        type="password"
        autoComplete="new-password"
        value={newPassword}
        onChange={onChangeNew}
        error={errors.newPassword}
      />
      <PasswordStrengthMeter password={newPassword} />
      <AccountField
        id="account-confirm-password"
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        value={confirmPassword}
        onChange={onChangeConfirm}
        error={errors.confirmPassword}
      />

      {success ? (
        <p className="text-sm font-medium text-emerald-600 dark:text-emerald-500" role="status">
          Password requirements met. (Backend not connected — nothing was saved.)
        </p>
      ) : null}

      <div className="pt-1">
        <Button type="submit" disabled={submitting}>
          {submitting ? "Updating…" : "Update password"}
        </Button>
      </div>
    </form>
  </section>
);
