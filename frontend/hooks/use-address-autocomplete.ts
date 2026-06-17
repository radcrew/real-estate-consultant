"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { GOOGLE_MAPS_API_KEY } from "@config/env";

import { loadPlacesLibrary } from "./use-location";

export type AddressSuggestion = {
  placeId: string;
  label: string;
};

/** Parsed parts populated from a selected place's address components. */
export type ParsedAddress = {
  address: string;
  city: string;
  state: string;
};

type AddressComponent = {
  types: string[];
  longText?: string;
  shortText?: string;
  long_name?: string;
  short_name?: string;
};

const componentValue = (
  components: AddressComponent[],
  type: string,
  short = false,
): string => {
  const match = components.find((c) => c.types?.includes(type));
  if (!match) return "";
  return short
    ? match.shortText ?? match.short_name ?? ""
    : match.longText ?? match.long_name ?? "";
};

const toParsedAddress = (components: AddressComponent[]): ParsedAddress => {
  const streetNumber = componentValue(components, "street_number");
  const route = componentValue(components, "route");
  const city =
    componentValue(components, "locality") ||
    componentValue(components, "postal_town") ||
    componentValue(components, "sublocality") ||
    componentValue(components, "administrative_area_level_2");
  const state = componentValue(components, "administrative_area_level_1", true);

  return {
    address: [streetNumber, route].filter(Boolean).join(" "),
    city,
    state,
  };
};

type UseAddressAutocompleteOptions = {
  initialQuery: string;
  /** Called as the user types — keeps the street-address field controlled. */
  onChange: (value: string) => void;
  /** Called once a place is selected and its components are resolved. */
  onSelect: (parsed: ParsedAddress) => void;
};

/**
 * Google Places autocomplete for a street-address field. Unlike `useLocation`
 * (locality-only, single string), this suggests full addresses and, on select,
 * resolves address components to fill street / city / state separately.
 */
export const useAddressAutocomplete = ({
  initialQuery,
  onChange,
  onSelect,
}: UseAddressAutocompleteOptions) => {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [isLoadingSuggestions, setLoadingSuggestions] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const placesLibRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sessionTokenRef = useRef<any>(null);
  const predictionByPlaceIdRef = useRef<Map<string, unknown>>(new Map());
  const suggestionsTimerRef = useRef<number | null>(null);
  const fetchGenerationRef = useRef(0);

  useEffect(() => {
    let isMounted = true;

    (async () => {
      if (!GOOGLE_MAPS_API_KEY) {
        if (isMounted) setLoadError("Location autocomplete is not configured.");
        return;
      }
      try {
        const placesLib = await loadPlacesLibrary(GOOGLE_MAPS_API_KEY);
        if (isMounted) placesLibRef.current = placesLib;
      } catch {
        if (isMounted) setLoadError("Unable to load location autocomplete.");
      }
    })();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(
    () => () => {
      if (suggestionsTimerRef.current != null) {
        window.clearTimeout(suggestionsTimerRef.current);
      }
    },
    [],
  );

  const fetchSuggestions = (input: string) => {
    const trimmed = input.trim();
    const placesLib = placesLibRef.current;

    if (!placesLib || trimmed.length < 3) {
      setLoadingSuggestions(false);
      setSuggestions([]);
      predictionByPlaceIdRef.current = new Map();
      return;
    }

    const { AutocompleteSuggestion, AutocompleteSessionToken } = placesLib;
    if (!AutocompleteSuggestion?.fetchAutocompleteSuggestions) {
      setLoadingSuggestions(false);
      return;
    }

    if (suggestionsTimerRef.current != null) {
      window.clearTimeout(suggestionsTimerRef.current);
    }

    setLoadingSuggestions(true);
    const gen = ++fetchGenerationRef.current;

    suggestionsTimerRef.current = window.setTimeout(() => {
      (async () => {
        if (!sessionTokenRef.current) {
          sessionTokenRef.current = new AutocompleteSessionToken();
        }

        try {
          const { suggestions: raw } =
            await AutocompleteSuggestion.fetchAutocompleteSuggestions({
              input: trimmed,
              sessionToken: sessionTokenRef.current,
              includedPrimaryTypes: ["street_address", "premise", "subpremise"],
            });

          if (gen !== fetchGenerationRef.current) return;

          const nextMap = new Map<string, unknown>();
          const nextList: AddressSuggestion[] = [];

          for (const item of raw ?? []) {
            const prediction = item?.placePrediction;
            if (!prediction) continue;

            const placeId: string | undefined =
              prediction.placeId ?? prediction.place_id;
            if (!placeId) continue;

            const label =
              prediction.text?.text ??
              [prediction.mainText?.text, prediction.secondaryText?.text]
                .filter(Boolean)
                .join(", ");
            if (!label) continue;

            nextMap.set(placeId, prediction);
            nextList.push({ placeId, label });
          }

          predictionByPlaceIdRef.current = nextMap;
          setSuggestions(nextList);
        } catch {
          if (gen === fetchGenerationRef.current) {
            setSuggestions([]);
            predictionByPlaceIdRef.current = new Map();
          }
        } finally {
          if (gen === fetchGenerationRef.current) {
            setLoadingSuggestions(false);
          }
        }
      })();
    }, 180);
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    onChange(value);
    fetchSuggestions(value);
  };

  const selectSuggestion = (suggestion: AddressSuggestion) => {
    setQuery(suggestion.label);
    setSuggestions([]);

    const prediction = predictionByPlaceIdRef.current.get(suggestion.placeId) as
      | {
          toPlace: () => {
            fetchFields: (o: { fields: string[] }) => Promise<void>;
            addressComponents?: AddressComponent[];
            formattedAddress?: string;
          };
        }
      | undefined;

    predictionByPlaceIdRef.current = new Map();

    if (!prediction || typeof prediction.toPlace !== "function") {
      onChange(suggestion.label);
      sessionTokenRef.current = null;
      return;
    }

    (async () => {
      try {
        const place = prediction.toPlace();
        await place.fetchFields({
          fields: ["addressComponents", "formattedAddress"],
        });

        const parsed = toParsedAddress(place.addressComponents ?? []);
        // Prefer the parsed street line; fall back to the suggestion label.
        const street = parsed.address || suggestion.label;
        setQuery(street);
        onSelect({ ...parsed, address: street });
      } catch {
        onChange(suggestion.label);
      } finally {
        sessionTokenRef.current = null;
      }
    })();
  };

  const showSuggestionList = useMemo(
    () => suggestions.length > 0 && query.trim().length >= 3,
    [query, suggestions.length],
  );

  return {
    query,
    suggestions,
    isLoadingSuggestions,
    loadError,
    showSuggestionList,
    handleQueryChange,
    selectSuggestion,
  };
};
