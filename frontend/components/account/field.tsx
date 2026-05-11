"use client";

import type { InputHTMLAttributes } from "react";

import { Input } from "@components/ui/input";
import { cn } from "@utils/common";

import { FIELD_INPUT_CLASS } from "@components/auth/fields/styles";

export type AccountFieldProps = {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string | null;
  readOnly?: boolean;
  type?: InputHTMLAttributes<HTMLInputElement>["type"];
  autoComplete?: string;
  disabled?: boolean;
  className?: string;
};

export const AccountField = ({
  id,
  label,
  value,
  onChange,
  error,
  readOnly,
  type = "text",
  autoComplete,
  disabled,
  className,
}: AccountFieldProps) => {
  const invalid = Boolean(error);

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label htmlFor={id} className="text-sm font-medium text-foreground">
        {label}
      </label>
      <Input
        id={id}
        name={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        disabled={disabled}
        aria-invalid={invalid}
        aria-describedby={invalid ? `${id}-error` : undefined}
        className={cn(
          FIELD_INPUT_CLASS,
          readOnly && "cursor-default bg-muted/40 text-foreground shadow-none",
        )}
      />
      {error ? (
        <p id={`${id}-error`} className="text-xs text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
};
