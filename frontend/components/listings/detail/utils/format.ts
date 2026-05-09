export const formatUsd = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: value >= 100 ? 0 : 2,
  }).format(value);
};

export const formatSqft = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return `${new Intl.NumberFormat("en-US").format(Math.round(value))} sq ft`;
};

export const formatFt = (value: number | null | undefined): string | null => {
  if (value == null || Number.isNaN(value)) {
    return null;
  }
  return `${value} ft`;
};
