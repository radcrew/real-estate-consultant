"use client";

import { Input } from "@components/ui/input";
import {
  useAddressAutocomplete,
  type ParsedAddress,
} from "../../hooks/use-address-autocomplete";

type AddressAutocompleteProps = {
  value: string;
  onChange: (value: string) => void;
  onSelect: (parsed: ParsedAddress) => void;
  className?: string;
};

/**
 * Street-address input backed by Google Places autocomplete. Selecting a
 * suggestion fills the street line here and reports parsed city/state to the
 * parent via `onSelect`.
 */
export const AddressAutocomplete = ({
  value,
  onChange,
  onSelect,
  className,
}: AddressAutocompleteProps) => {
  const {
    query,
    suggestions,
    isLoadingSuggestions,
    loadError,
    showSuggestionList,
    handleQueryChange,
    selectSuggestion,
  } = useAddressAutocomplete({
    initialQuery: value,
    onChange,
    onSelect,
  });

  return (
    <div className={`relative ${className ?? ""}`}>
      <Input
        autoComplete="off"
        placeholder="Start typing an address…"
        value={query}
        onChange={(e) => handleQueryChange(e.target.value)}
      />

      {loadError && (
        <p className="mt-1 text-xs text-neutral-400">{loadError}</p>
      )}

      {isLoadingSuggestions && (
        <p className="mt-1 text-xs text-neutral-400">Searching addresses…</p>
      )}

      {showSuggestionList && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-900">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.placeId}
              type="button"
              className="block w-full cursor-pointer px-4 py-2.5 text-left text-sm text-neutral-700 hover:bg-neutral-100 dark:text-neutral-200 dark:hover:bg-neutral-800"
              onClick={() => selectSuggestion(suggestion)}
            >
              {suggestion.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
