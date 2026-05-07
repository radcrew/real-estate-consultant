import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export type FormatMoneyOptions = {
  integerThreshold?: number;
};

export function formatMoney(value: number, options?: FormatMoneyOptions): string {
  const threshold = options?.integerThreshold ?? 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: Math.abs(value) >= threshold ? 0 : 2,
  }).format(value);
}

export function formatMetricNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 2,
    notation: Math.abs(value) >= 1e6 ? "compact" : "standard",
  }).format(value);
}

export function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}
