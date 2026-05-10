"use client";

import { cn } from "@utils/common";

import { passwordStrengthLabel, scorePasswordStrength } from "@lib/account-validation";

type PasswordStrengthMeterProps = {
  password: string;
  className?: string;
};

const SEGMENTS = 4;

export const PasswordStrengthMeter = ({ password, className }: PasswordStrengthMeterProps) => {
  const score = scorePasswordStrength(password);
  const label = passwordStrengthLabel(score);

  return (
    <div className={cn("flex flex-col gap-2", className)} aria-live="polite">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-muted-foreground">Password strength</span>
        <span
          className={cn(
            "text-xs font-semibold",
            score <= 1 && "text-destructive",
            score === 2 && "text-amber-600 dark:text-amber-500",
            score >= 3 && "text-emerald-600 dark:text-emerald-500",
          )}
        >
          {password ? label : "—"}
        </span>
      </div>
      <div className="flex gap-1" role="meter" aria-valuemin={0} aria-valuemax={SEGMENTS} aria-valuenow={score}>
        {Array.from({ length: SEGMENTS }, (_, i) => (
          <span
            key={i}
            className={cn(
              "h-1.5 min-w-0 flex-1 rounded-sm transition-colors",
              i < score
                ? score <= 1
                  ? "bg-destructive/80"
                  : score === 2
                    ? "bg-amber-500"
                    : "bg-emerald-500"
                : "bg-muted",
            )}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Use at least 8 characters, mixing uppercase, lowercase, numbers, and symbols for a stronger password.
      </p>
    </div>
  );
};
