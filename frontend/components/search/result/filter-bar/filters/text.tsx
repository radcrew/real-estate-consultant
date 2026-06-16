"use client";

import { ChevronDown, X } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@components/ui/dropdown-menu";
import { Input } from "@components/ui/input";
import { useLocation } from "@hooks/use-location";
import { cn } from "@utils/common";

import { FILTER_BAR_PILL, FILTER_BAR_PILL_ACTIVE } from "./styles";

const STATUS_TEXT = "mt-2 text-xs text-neutral-500 dark:text-neutral-400";
import { stopMenuKeyboardCapture, stopMenuTriggerBubble } from "./utils";

type TextFilterProps = {
  fieldKey: string;
  label: string;
  value: string;
  onChange: (next: string) => void;
  disabled?: boolean;
  className?: string;
};

export const TextFilter = ({ fieldKey, label, value, onChange, disabled, className }: TextFilterProps) => {
  const {
    query,
    suggestions,
    isLoadingSuggestions,
    loadError,
    showSuggestionList,
    placesHostRef,
    handleQueryChange,
    selectSuggestion,
  } = useLocation({
    initialQuery: value,
    onChange,
  });

  const hasValue = value.trim().length > 0;
  const display = hasValue ? value.trim() : label;

  const handleClear = (e: { preventDefault: () => void; stopPropagation: () => void }) => {
    stopMenuTriggerBubble(e);
    onChange("");
  };

  return (
    <DropdownMenu modal={false}>
      <DropdownMenuTrigger
        disabled={disabled}
        aria-label={hasValue ? `${label}: ${display}` : label}
        className={cn(
          FILTER_BAR_PILL,
          hasValue && FILTER_BAR_PILL_ACTIVE,
          "disabled:pointer-events-none disabled:opacity-50",
          className,
        )}
      >
        <span className="min-w-0 flex-1 truncate text-left">{display}</span>
        {hasValue ? (
          <span
            title={`Clear ${label}`}
            className="-mr-1 flex size-8 shrink-0 cursor-default items-center justify-center rounded-sm text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-100"
            onPointerDown={stopMenuTriggerBubble}
            onClick={handleClear}
          >
            <X className="size-4 shrink-0" aria-hidden />
          </span>
        ) : (
          <ChevronDown className="size-4 shrink-0 text-neutral-500 dark:text-neutral-400 pointer-events-none" aria-hidden />
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="bottom" sideOffset={6} className="w-[min(20rem,calc(100vw-2rem))] p-3">
        <label className="text-xs font-medium text-neutral-500 dark:text-neutral-400" htmlFor={`${fieldKey}-text`}>
          {label}
        </label>
        <Input
          id={`${fieldKey}-text`}
          type="text"
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          onKeyDownCapture={stopMenuKeyboardCapture}
          disabled={disabled}
          className="mt-2"
          placeholder={label}
          autoFocus
        />

        {loadError ? (
          <p className={STATUS_TEXT}>{loadError}</p>
        ) : null}

        {isLoadingSuggestions ? (
          <p className={STATUS_TEXT}>Searching locations...</p>
        ) : null}

        {showSuggestionList ? (
          <div className="mt-2 rounded-md border border-neutral-200/70 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.placeId}
                type="button"
                className="block w-full cursor-pointer px-3 py-2 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
                onClick={() => selectSuggestion(suggestion)}
              >
                {suggestion.label}
              </button>
            ))}
          </div>
        ) : null}

        <div ref={placesHostRef} className="hidden" />
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
