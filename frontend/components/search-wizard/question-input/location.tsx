"use client";

import { Input } from "@components/ui/input";

import type { LocationQuestion } from "../types";
import { useLocation } from "../../../hooks/use-location";

type LocationQuestionInputProps = {
  question: LocationQuestion;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  answer: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange: (value: any) => void;
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
        className="h-9 border-border/80 bg-background px-3 text-sm"
      />

      {loadError && <p className="text-xs text-muted-foreground">{loadError}</p>}

      {isLoadingSuggestions && (
        <p className="text-xs text-muted-foreground">Searching locations...</p>
      )}

      {showSuggestionList && (
        <div className="rounded-md border border-border/70 bg-background shadow-sm">
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
      )}

      <div ref={placesHostRef} className="hidden" />
    </div>
  );
};
