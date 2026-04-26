import type { ChangeEvent } from "react";
import { Input } from "@components/ui/input";

type NumberFieldProps = {
  id: string;
  label: string;
  value: number | null;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
};

export const NumberField = ({
  id,
  label,
  value,
  onChange,
}: NumberFieldProps) => (
  <div className="space-y-1.5">
    <label htmlFor={id} className="text-sm font-medium">
      {label}
    </label>
    <Input
      id={id}
      type="number"
      inputMode="numeric"
      value={value ?? ""}
      onChange={onChange}
      className="h-9 border-border/80 bg-background px-3 text-sm"
    />
  </div>
);