"use client";

import { useEffect, useMemo, useRef, useState } from "react";

declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    google?: any;
  }
}

type LocationSuggestion = {
  placeId: string;
  label: string;
};

const GOOGLE_MAPS_SCRIPT_ID = "google-maps-places-script";

const loadGooglePlacesApi = async (apiKey: string) => {
  if (typeof window === "undefined") return;
  if (window.google?.maps?.places) return;

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
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps"));
    document.head.appendChild(script);
  });
};

const getComponentValue = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  components: any[] | undefined,
  targetType: string,
) =>
  components?.find((component) => component.types?.includes(targetType))
    ?.long_name;

const mapPlaceResultToLocation = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  result: any,
  fallbackLabel: string,
) => ({
  label: result.formatted_address ?? fallbackLabel,
  city:
    getComponentValue(result.address_components, "locality") ??
    getComponentValue(result.address_components, "administrative_area_level_2"),
  state: getComponentValue(result.address_components, "administrative_area_level_1"),
  country: getComponentValue(result.address_components, "country"),
});

type UseLocationOptions = {
  initialQuery: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onChange: (value: any) => void;
};

export const useLocation = ({ initialQuery, onChange }: UseLocationOptions) => {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isLoadingSuggestions, setLoadingSuggestions] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const autocompleteServiceRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const placesServiceRef = useRef<any>(null);
  const placesHostRef = useRef<HTMLDivElement | null>(null);
  const suggestionsTimerRef = useRef<number | null>(null);

  const googleMapsApiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

  useEffect(() => {
    let isMounted = true;

    const initialize = async () => {
      if (!googleMapsApiKey) {
        if (isMounted) setLoadError("Location autocomplete is not configured.");
        return;
      }

      try {
        await loadGooglePlacesApi(googleMapsApiKey);
        if (!isMounted || !window.google?.maps?.places) return;

        autocompleteServiceRef.current =
          new window.google.maps.places.AutocompleteService();
        placesServiceRef.current = new window.google.maps.places.PlacesService(
          placesHostRef.current ?? document.createElement("div"),
        );
      } catch {
        if (isMounted) setLoadError("Unable to load location autocomplete.");
      }
    };

    initialize();
    return () => {
      isMounted = false;
    };
  }, [googleMapsApiKey]);

  useEffect(
    () => () => {
      if (suggestionsTimerRef.current != null) {
        window.clearTimeout(suggestionsTimerRef.current);
      }
    },
    [],
  );

  const fetchSuggestions = (input: string) => {
    const autocompleteService = autocompleteServiceRef.current;
    if (!autocompleteService || input.trim().length < 2) {
      setLoadingSuggestions(false);
      return;
    }

    if (suggestionsTimerRef.current != null) {
      window.clearTimeout(suggestionsTimerRef.current);
    }

    setLoadingSuggestions(true);
    suggestionsTimerRef.current = window.setTimeout(() => {
      autocompleteService.getPlacePredictions(
        { input, types: ["(cities)"] },
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (predictions: any[] | null) => {
          setLoadingSuggestions(false);
          setSuggestions(
            (predictions ?? []).map((prediction) => ({
              placeId: prediction.place_id,
              label: prediction.description,
            })),
          );
        },
      );
    }, 180);
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    setSuggestions([]);
    fetchSuggestions(value);
    onChange({ input: value });
  };

  const selectSuggestion = (suggestion: LocationSuggestion) => {
    const placesService = placesServiceRef.current;
    setQuery(suggestion.label);
    setSuggestions([]);

    if (!placesService) {
      onChange({ label: suggestion.label, input: suggestion.label });
      return;
    }

    placesService.getDetails(
      {
        placeId: suggestion.placeId,
        fields: ["formatted_address", "address_components"],
      },
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (result: any, status: any) => {
        if (status !== window.google.maps.places.PlacesServiceStatus.OK || !result) {
          onChange({ label: suggestion.label, input: suggestion.label });
          return;
        }

        onChange({
          ...mapPlaceResultToLocation(result, suggestion.label),
          input: suggestion.label,
        });
      },
    );
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
