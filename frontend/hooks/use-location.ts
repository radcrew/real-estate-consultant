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

const GOOGLE_MAPS_SCRIPT_ID = "google-maps-bootstrap";

const loadGoogleMapsBootstrap = async (apiKey: string) => {
  if (typeof window === "undefined") return;
  if (window.google?.maps?.importLibrary) return;

  const existing = document.getElementById(GOOGLE_MAPS_SCRIPT_ID);
  if (existing) {
    await new Promise<void>((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(), { once: true });
    });
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.id = GOOGLE_MAPS_SCRIPT_ID;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}&loading=async`;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps"));
    document.head.appendChild(script);
  });
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

  useEffect(() => {
    let isMounted = true;

    const initialize = async () => {
      if (!GOOGLE_MAPS_API_KEY) {
        if (isMounted) setLoadError("Location autocomplete is not configured.");
        return;
      }

      try {
        await loadGoogleMapsBootstrap(GOOGLE_MAPS_API_KEY);
        if (!isMounted || !window.google?.maps?.importLibrary) return;

        const placesLib = await window.google.maps.importLibrary("places");
        if (!isMounted) return;
        placesLibRef.current = placesLib;
      } catch {
        if (isMounted) setLoadError("Unable to load location autocomplete.");
      }
    };

    initialize();
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
    setSuggestions([]);
    predictionByPlaceIdRef.current = new Map();
    fetchSuggestions(value);
    onChange(value);
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
