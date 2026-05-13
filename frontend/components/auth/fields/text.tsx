"use client";

import type { ChangeEvent } from "react";

import { Input } from "@components/ui/input";

import { FIELD_INPUT_CLASS } from "./styles";

export type TextFieldProps = {
  id: string;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  name?: string;
  label: string;
  autoComplete?: string;
  disabled?: boolean;
  type?: "text";
};

export const TextField = ({
  id,
  value,
  onChange,
  name,
  label,
  autoComplete,
  disabled,
  type = "text",
}: TextFieldProps) => (
  <div className="flex flex-col gap-1.5">
    <label htmlFor={id} className="text-sm font-medium">
      {label}
    </label>
    <Input
      id={id}
      name={name ?? id}
      type={type}
      autoComplete={autoComplete}
      required
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={FIELD_INPUT_CLASS}
    />
  </div>
);
