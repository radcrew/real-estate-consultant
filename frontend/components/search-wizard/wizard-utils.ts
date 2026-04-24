import type { AnswerValue, SummaryRow, WizardAnswers, WizardQuestion } from "./types";

export const formatRangeValue = (value: number, unit?: string) => {
  if (unit === "$") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(value);
  }

  if (unit === "SF") {
    return `${new Intl.NumberFormat("en-US").format(value)} SF`;
  }

  return `${value}${unit ? ` ${unit}` : ""}`;
};

