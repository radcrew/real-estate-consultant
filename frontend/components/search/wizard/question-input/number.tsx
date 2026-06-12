import type { ChangeEvent } from "react";
import { Input } from "@components/ui/input";

type NumberFieldProps = {
  id: string;
  label: string;
  value: number | null;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  autoFocus?: boolean;
  min?: number;
  placeholder?: string;
};

export const NumberField = ({
  id,
  label,
  value,
  onChange,
  autoFocus = false,
  min = 0,
  placeholder,
}: NumberFieldProps) => (
  <div className="space-y-1.5">
    <label htmlFor={id} className="text-sm font-medium">
      {label}
    </label>
    <Input
      id={id}
      type="number"
      inputMode="numeric"
      min={min}
      value={value ?? ""}
      onChange={onChange}
      autoFocus={autoFocus}
      placeholder={placeholder}
    />
  </div>
);