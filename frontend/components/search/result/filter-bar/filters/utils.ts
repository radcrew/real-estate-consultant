import type { KeyboardEvent as ReactKeyboardEvent } from "react";

import { formatMetricNumber, formatMoney } from "@lib/utils";
import type { RangeCriterionData } from "@lib/search-criteria";


export function stopMenuTriggerBubble(e: { preventDefault: () => void; stopPropagation: () => void }): void {
  e.preventDefault();
  e.stopPropagation();
}

export function stopMenuKeyboardCapture(e: ReactKeyboardEvent): void {
  e.stopPropagation();
}

export function isRangeInvalid(value: RangeCriterionData): boolean {
  return Number.isFinite(value.min) && Number.isFinite(value.max) && value.min > value.max;
}


export function rangePriceTriggerText(value: RangeCriterionData, label: string, unit?: string): string {
  const u = unit?.trim();
  const priceMoneyPrefix = u ? `${u} ` : "USD ";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  const hasMin = Number.isFinite(value.min);
  const hasMax = Number.isFinite(value.max);

  if (hasBounds) {
    return `${priceMoneyPrefix}${formatMoney(value.min, { integerThreshold: 1000 })} – ${formatMoney(value.max, { integerThreshold: 1000 })}`;
  }
  if (hasMin) {
    return `From ${formatMoney(value.min, { integerThreshold: 1000 })}`;
  }
  if (hasMax) {
    return `Up to ${formatMoney(value.max, { integerThreshold: 1000 })}`;
  }
  if (u) {
    return `${label} (${u})`;
  }
  return label;
}

export function rangeNormalTriggerText(value: RangeCriterionData, label: string, unit?: string): string {
  const u = unit?.trim();
  const suffix = u ? ` ${u}` : "";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  const hasMin = Number.isFinite(value.min);
  const hasMax = Number.isFinite(value.max);

  if (hasBounds) {
    return `${formatMetricNumber(value.min)} – ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (hasMin) {
    return `From ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (hasMax) {
    return `Up to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (u) {
    return `${label} (${u})`;
  }
  return label;
}

export function rangePriceSummaryForAria(value: RangeCriterionData): string {
  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    return `${formatMoney(value.min, { integerThreshold: 1000 })} to ${formatMoney(value.max, { integerThreshold: 1000 })}`;
  }
  if (Number.isFinite(value.min)) {
    return `minimum ${formatMoney(value.min, { integerThreshold: 1000 })}`;
  }
  if (Number.isFinite(value.max)) {
    return `maximum ${formatMoney(value.max, { integerThreshold: 1000 })}`;
  }
  return "Not set";
}

export function rangeNormalSummaryForAria(value: RangeCriterionData, unit?: string): string {
  const u = unit?.trim();
  const suffix = u ? ` ${u}` : "";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    return `${formatMetricNumber(value.min)} to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (Number.isFinite(value.min)) {
    return `minimum ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (Number.isFinite(value.max)) {
    return `maximum ${formatMetricNumber(value.max)}${suffix}`;
  }
  return "Not set";
}
