"use client";

import { Building2, Factory, Store } from "lucide-react";

import { cn } from "@lib/utils";

import { styles } from "./styles";

type SelectOptionCardProps = {
  label: string;
  hint?: string;
  selected: boolean;
  onClick: () => void;
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
}: SelectOptionCardProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      styles.card,
      selected ? styles.cardSelected : styles.cardIdle,
    )}
  >
    <span
      className={cn(
        styles.iconWrap,
        selected ? styles.iconWrapSelected : styles.iconWrapIdle,
      )}
    >
      <SelectOptionIcon label={label} />
    </span>

    <div className={styles.textColumn}>
      <p className={styles.label}>{label}</p>
      <span className={styles.hint}>{hint}</span>
    </div>
  </button>
);
