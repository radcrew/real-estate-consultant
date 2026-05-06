import type { KeyboardEvent as ReactKeyboardEvent } from "react";

import { formatMetricNumber, formatMoney } from "@lib/utils";
import type { RangeCriterionData } from "@lib/search-criteria";

/**
 * Prevents nested clear hit targets from toggling the menu trigger
 * (Base UI menu can open on pointer down).
 */
export function stopMenuTriggerBubble(e: { preventDefault: () => void; stopPropagation: () => void }): void {
  e.preventDefault();
  e.stopPropagation();
}

/** Stops Menu composite/typeahead from swallowing keys meant for inputs inside the popup. */
export function stopMenuKeyboardCapture(e: ReactKeyboardEvent): void {
  e.stopPropagation();
}

function isPriceRangeLabel(label: string): boolean {
  const k = label.trim().toLowerCase();
  return k === "price" || k.includes("price");
}

export function isRangeInvalid(value: RangeCriterionData): boolean {
  return Number.isFinite(value.min) && Number.isFinite(value.max) && value.min > value.max;
}

/**
 * Chip label for a range filter. Number style follows the criterion **label** (e.g. Price vs Size);
 * ``unit`` is only used as a suffix for dimension-style rows (e.g. size).
 */
export function rangeTriggerText(value: RangeCriterionData, label: string, unit?: string): string {
  const price = isPriceRangeLabel(label);
  const u = unit?.trim();
  const suffix = u ? ` ${u}` : "";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  const hasMin = Number.isFinite(value.min);
  const hasMax = Number.isFinite(value.max);

  if (hasBounds) {
    if (price) {
      return `USD ${formatMoney(value.min, { integerThreshold: 1000 })} – ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    return `${formatMetricNumber(value.min)} – ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (hasMin) {
    if (price) {
      return `From ${formatMoney(value.min, { integerThreshold: 1000 })}`;
    }
    return `From ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (hasMax) {
    if (price) {
      return `Up to ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    return `Up to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (u) {
    return `${label} (${u})`;
  }
  return label;
}

export function rangeSummaryForAria(value: RangeCriterionData, label: string, unit?: string): string {
  const price = isPriceRangeLabel(label);
  const u = unit?.trim();
  const suffix = u ? ` ${u}` : "";

  const hasBounds = Number.isFinite(value.min) && Number.isFinite(value.max);
  if (hasBounds) {
    if (price) {
      return `${formatMoney(value.min, { integerThreshold: 1000 })} to ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    return `${formatMetricNumber(value.min)} to ${formatMetricNumber(value.max)}${suffix}`;
  }
  if (Number.isFinite(value.min)) {
    if (price) {
      return `minimum ${formatMoney(value.min, { integerThreshold: 1000 })}`;
    }
    return `minimum ${formatMetricNumber(value.min)}${suffix}`;
  }
  if (Number.isFinite(value.max)) {
    if (price) {
      return `maximum ${formatMoney(value.max, { integerThreshold: 1000 })}`;
    }
    return `maximum ${formatMetricNumber(value.max)}${suffix}`;
  }
  return "Not set";
}
