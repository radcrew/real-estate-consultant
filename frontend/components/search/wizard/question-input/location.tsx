"use client";

import { Input } from "@components/ui/input";

import type { LocationQuestion } from "../types";
import { useLocation } from "../../../../hooks/use-location";

type LocationQuestionInputProps = {
  question: LocationQuestion;
  answer: string;
  onChange: (value: string) => void;
};

export const LocationQuestionInput = ({
  question,
  answer,
  onChange,
}: LocationQuestionInputProps) => {
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
    initialQuery: answer,
    onChange,
  });

  return (
    <div className="space-y-2">
      <Input
        id={question.id}
        value={query}
        autoFocus
        onChange={(event) => {
          handleQueryChange(event.target.value);
        }}
      />

      {loadError && <p className="text-xs text-muted-foreground">{loadError}</p>}

      {isLoadingSuggestions && (
        <p className="text-xs text-muted-foreground">Searching locations...</p>
      )}

      {showSuggestionList && (
        <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.placeId}
              type="button"
              className="block w-full cursor-pointer px-4 py-2.5 text-left text-sm hover:bg-neutral-100 dark:hover:bg-neutral-800"
              onClick={() => selectSuggestion(suggestion)}
            >
              {suggestion.label}
            </button>
          ))}
        </div>
      )}

      <div ref={placesHostRef} className="hidden" />
    </div>
  );
};
