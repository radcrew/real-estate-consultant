"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { GOOGLE_MAPS_API_KEY } from "@lib/config";

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
  }
}

export type LocationSuggestion = {
  placeId: string;
  label: string;
};

// Shared promise so every hook instance (including StrictMode remounts) awaits the same load.
let _placesLibPromise: Promise<unknown> | null = null;

const loadPlacesLibrary = (apiKey: string): Promise<unknown> => {
  if (_placesLibPromise) return _placesLibPromise;

  _placesLibPromise = new Promise<unknown>((resolve, reject) => {
    if (typeof window === "undefined") {
      resolve(null);
      return;
    }

    // Already loaded — grab the places library directly.
    if (window.google?.maps?.places) {
      resolve(window.google.maps.places);
      return;
    }

    const script = document.createElement("script");
    // Classic (non-async) load with libraries=places — window.google.maps.places
    // is fully available synchronously by the time onload fires, no importLibrary needed.
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&libraries=places`;
    script.async = true;
    script.onload = () => {
      if (window.google?.maps?.places) {
        resolve(window.google.maps.places);
      } else {
        _placesLibPromise = null;
        reject(new Error("Google Maps did not initialize correctly"));
      }
    };
    script.onerror = () => {
      _placesLibPromise = null;
      reject(new Error("Failed to load Google Maps"));
    };
    document.head.appendChild(script);
  });

  return _placesLibPromise;
};

type UseLocationOptions = {
  initialQuery: string;
  onChange: (value: string) => void;
};

export const useLocation = ({ initialQuery, onChange }: UseLocationOptions) => {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isLoadingSuggestions, setLoadingSuggestions] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const placesLibRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sessionTokenRef = useRef<any>(null);
  const predictionByPlaceIdRef = useRef<Map<string, unknown>>(new Map());
  const suggestionsTimerRef = useRef<number | null>(null);
  const fetchGenerationRef = useRef(0);
  const placesHostRef = useRef<HTMLDivElement | null>(null);
  const queryRef = useRef(initialQuery);

  useEffect(() => {
    setQuery(initialQuery);
    queryRef.current = initialQuery;
    setSuggestions([]);
    predictionByPlaceIdRef.current = new Map();
  }, [initialQuery]);

  useEffect(() => {
    let isMounted = true;

    const initialize = async () => {
      if (!GOOGLE_MAPS_API_KEY) {
        if (isMounted) setLoadError("Location autocomplete is not configured.");
        return;
      }

      try {
        const placesLib = await loadPlacesLibrary(GOOGLE_MAPS_API_KEY);
        if (!isMounted) return;
        placesLibRef.current = placesLib;

        if (queryRef.current.trim().length >= 2) {
          fetchSuggestions(queryRef.current);
        }
      } catch {
        if (isMounted) setLoadError("Unable to load location autocomplete.");
      }
    };

    initialize();
    return () => {
      isMounted = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
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

    if (!placesLib || trimmed.length < 2) {
      setLoadingSuggestions(false);
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
          const { suggestions: raw } = await AutocompleteSuggestion.fetchAutocompleteSuggestions({
            input: trimmed,
            sessionToken: sessionTokenRef.current,
            includedPrimaryTypes: ["locality"],
          });

          if (gen !== fetchGenerationRef.current) {
            return;
          }

          const nextMap = new Map<string, unknown>();
          const nextList: LocationSuggestion[] = [];

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
    queryRef.current = value;
    onChange(value);
    setSuggestions([]);
    predictionByPlaceIdRef.current = new Map();
    fetchSuggestions(value);
  };

  const selectSuggestion = (suggestion: LocationSuggestion) => {
    setQuery(suggestion.label);
    setSuggestions([]);

    const prediction = predictionByPlaceIdRef.current.get(suggestion.placeId) as
      | {
          toPlace: () => {
            fetchFields: (o: { fields: string[] }) => Promise<void>;
            formattedAddress?: string;
            displayName?: string;
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
          fields: ["formattedAddress", "displayName"],
        });

        const formatted = place.formattedAddress ?? place.displayName ?? suggestion.label;

        onChange(String(formatted));
      } catch {
        onChange(suggestion.label);
      } finally {
        sessionTokenRef.current = null;
      }
    })();
  };

  const showSuggestionList = useMemo(
    () => suggestions.length > 0 && query.trim().length >= 2,
    [query, suggestions.length],
  );

  return {
    query,
    suggestions,
    isLoadingSuggestions,
    loadError,
    showSuggestionList,
    placesHostRef,
    handleQueryChange,
    selectSuggestion,
  };
};
