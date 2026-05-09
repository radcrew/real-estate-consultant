"use client";

import { Building2, Factory, Store } from "lucide-react";

import { cn } from "@utils/common";

import { STYLES } from "./styles";

type SelectOptionCardProps = {
  label: string;
  hint?: string;
  selected: boolean;
  onClick: () => void;
  autoFocus?: boolean;
};

const SELECT_OPTION_ICON_MAP = {
  industrial: Factory,
  flex: Factory,
  retail: Store,
} as const;

const SelectOptionIcon = ({ label }: { label: string }) => {
  const normalizedLabel = label.toLowerCase();
  const Icon =
    Object.entries(SELECT_OPTION_ICON_MAP).find(([key]) =>
      normalizedLabel.includes(key),
    )?.[1] ?? Building2;

  return <Icon className="size-5" aria-hidden />;
};

export const SelectOptionCard = ({
  label,
  hint,
  selected,
  onClick,
  autoFocus = false,
}: SelectOptionCardProps) => (
  <button
    type="button"
    autoFocus={autoFocus}
    onClick={onClick}
    className={cn(
      STYLES.card,
      selected ? STYLES.cardSelected : STYLES.cardIdle,
    )}
  >
    <span
      className={cn(
        STYLES.iconWrap,
        selected ? STYLES.iconWrapSelected : STYLES.iconWrapIdle,
      )}
    >
      <SelectOptionIcon label={label} />
    </span>

    <div className={STYLES.textColumn}>
      <p className={STYLES.label}>{label}</p>
      <span className={STYLES.hint}>{hint}</span>
    </div>
  </button>
);
