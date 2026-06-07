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
            className="-mr-1 flex size-8 shrink-0 cursor-default items-center justify-center rounded-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            onPointerDown={stopMenuTriggerBubble}
            onClick={handleClear}
          >
            <X className="size-4 shrink-0" aria-hidden />
          </span>
        ) : (
          <ChevronDown className="size-4 shrink-0 text-muted-foreground pointer-events-none" aria-hidden />
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="bottom" sideOffset={6} className="w-[min(20rem,calc(100vw-2rem))] p-3">
        <label className="text-xs font-medium text-muted-foreground" htmlFor={`${fieldKey}-text`}>
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
          <p className="mt-2 text-xs text-muted-foreground">{loadError}</p>
        ) : null}

        {isLoadingSuggestions ? (
          <p className="mt-2 text-xs text-muted-foreground">Searching locations...</p>
        ) : null}

        {showSuggestionList ? (
          <div className="mt-2 rounded-md border border-border/70 bg-background shadow-sm">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.placeId}
                type="button"
                className="block w-full cursor-pointer px-3 py-2 text-left text-sm hover:bg-muted"
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
