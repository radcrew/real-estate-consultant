"use client";

import { Building2, Factory, Store } from "lucide-react";

import { cn } from "@lib/utils";

type SelectOptionCardProps = {
  label: string;
  hint?: string;
  selected: boolean;
  onClick: () => void;
};

const CARD_CLASSNAME =
  "group relative grid min-h-24 grid-rows-[auto_auto_1fr] items-start justify-items-center overflow-hidden rounded-xl border px-3 py-3.5 text-center transition-all duration-200";
const CARD_IDLE_CLASSNAME =
  "border-slate-200/90 bg-white shadow-[0_8px_24px_-18px_rgba(15,23,42,0.35)] hover:-translate-y-0.5 hover:border-amber-300/70 hover:shadow-[0_20px_45px_-28px_rgba(245,158,11,0.45)]";
const CARD_SELECTED_CLASSNAME =
  "border-amber-400 bg-[linear-gradient(180deg,rgba(255,251,235,0.98),rgba(255,247,237,0.96))] shadow-[0_18px_40px_-24px_rgba(245,158,11,0.6)]";
const ICON_WRAP_CLASSNAME =
  "mb-2 inline-flex size-9 items-center justify-center rounded-lg border transition-colors";
const ICON_WRAP_IDLE_CLASSNAME =
  "border-slate-200 bg-slate-50 text-slate-500 group-hover:border-amber-200 group-hover:bg-amber-50 group-hover:text-amber-500";
const ICON_WRAP_SELECTED_CLASSNAME =
  "border-amber-200 bg-amber-50 text-amber-500";
const LABEL_CLASSNAME = "text-sm font-semibold tracking-tight text-slate-950";
const HINT_CLASSNAME = "mt-1.5 text-xs leading-relaxed text-slate-500";

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
      CARD_CLASSNAME,
      selected
        ? CARD_SELECTED_CLASSNAME
        : CARD_IDLE_CLASSNAME,
    )}
  >
    <span
      className={cn(
        ICON_WRAP_CLASSNAME,
        selected ? ICON_WRAP_SELECTED_CLASSNAME : ICON_WRAP_IDLE_CLASSNAME,
      )}
    >
      <SelectOptionIcon label={label} />
    </span>

    <div className="flex h-full w-full flex-col">
      <p className={LABEL_CLASSNAME}>{label}</p>
      <span className={HINT_CLASSNAME}>{hint}</span>
    </div>
  </button>
);
