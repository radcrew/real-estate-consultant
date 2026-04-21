"use client";

import type { ChangeEvent } from "react";

import { Input } from "@components/ui/input";

import { FIELD_INPUT_CLASS } from "./styles";

export type EmailFieldProps = {
  id: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  name?: string;
  label?: string;
  disabled?: boolean;
};

export const EmailField = ({
  id,
  value,
  onChange,
  name = "email",
  label = "Email",
  disabled,
}: EmailFieldProps) => (
  <div className="flex flex-col gap-1.5">
    <label htmlFor={id} className="text-sm font-medium">
      {label}
    </label>
    <Input
      id={id}
      name={name}
      type="email"
      autoComplete="email"
      required
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={FIELD_INPUT_CLASS}
    />
  </div>
);
