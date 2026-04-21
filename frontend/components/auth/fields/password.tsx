"use client";

import type { ChangeEvent, ReactNode } from "react";

import { Input } from "@components/ui/input";

import { FIELD_INPUT_CLASS } from "./styles";

export type PasswordFieldProps = {
  id: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  autoComplete: "current-password" | "new-password";
  label?: string;
  name?: string;
  minLength?: number;
  maxLength?: number;
  disabled?: boolean;
  children?: ReactNode;
};

export const PasswordField = ({
  id,
  value,
  onChange,
  autoComplete,
  label = "Password",
  name = "password",
  minLength = 8,
  maxLength = 72,
  disabled,
  children,
}: PasswordFieldProps) => (
  <div className="flex flex-col gap-1.5">
    <label htmlFor={id} className="text-sm font-medium">
      {label}
    </label>
    <Input
      id={id}
      name={name}
      type="password"
      autoComplete={autoComplete}
      required
      minLength={minLength}
      maxLength={maxLength}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={FIELD_INPUT_CLASS}
    />
    {children}
  </div>
);
