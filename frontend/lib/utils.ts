import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]) => twMerge(clsx(inputs));

export type FormatMoneyOptions = {
  integerThreshold?: number;
};

/** USD currency (en-US). Fewer decimals for larger magnitudes. */
export function formatMoney(value: number, options?: FormatMoneyOptions): string {
  const threshold = options?.integerThreshold ?? 100;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: Math.abs(value) >= threshold ? 0 : 2,
  }).format(value);
}

/**
 * Grouped plain number for metrics (e.g. range chips without currency):
 * compact notation from 1M+, fewer decimals from 1k+.
 */
export function formatMetricNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: Math.abs(value) >= 1000 ? 0 : 2,
    notation: Math.abs(value) >= 1e6 ? "compact" : "standard",
  }).format(value);
}

/** Grouped whole number (e.g. square feet). */
export function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}
