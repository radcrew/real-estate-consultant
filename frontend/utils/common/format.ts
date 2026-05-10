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

export function formatMoneyOrNull(
  value: number | null | undefined,
  options?: FormatMoneyOptions,
): string | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return formatMoney(value, options);
}

export function formatSqft(value: number | null | undefined): string | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return `${formatInteger(Math.round(value))} sq ft`;
}

export function formatFeet(value: number | null | undefined): string | null {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return `${value} ft`;
}
