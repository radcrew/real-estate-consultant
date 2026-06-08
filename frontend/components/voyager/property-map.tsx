"use client";

import GoogleMapReact from "google-map-react";

import type { PropertyModel } from "@components/voyager/listing-model";
import { GOOGLE_MAPS_API_KEY } from "@lib/config";
import { cn } from "@utils/common";

/**
 * Voyager-style listings map. Renders price-pill markers from
 * `PropertyModel.map` (lat/lng) via `google-map-react`, using the existing
 * `GOOGLE_MAPS_API_KEY`. Note: google-map-react officially targets React 16–18;
 * on React 19 it installs with a peer-dep warning — verify rendering at runtime.
 */
const US_CENTER = { lat: 39.5, lng: -98.35 };

interface PriceMarkerProps {
  lat: number;
  lng: number;
  label: string;
  active?: boolean;
  onClick?: () => void;
}

const PriceMarker = ({ label, active, onClick }: PriceMarkerProps) => (
  <button
    type="button"
    onClick={onClick}
    className={cn(
      "-translate-x-1/2 -translate-y-1/2 rounded-full px-2.5 py-1 text-xs font-semibold whitespace-nowrap shadow-md transition-colors focus:outline-none",
      active
        ? "bg-primary-600 text-white"
        : "bg-white text-neutral-900 hover:bg-primary-600 hover:text-white dark:bg-neutral-800 dark:text-white",
    )}
  >
    {label}
  </button>
);

export interface PropertyMapProps {
  items: PropertyModel[];
  activeId?: string;
  onMarkerClick?: (id: string) => void;
  defaultZoom?: number;
  className?: string;
}

export const PropertyMap = ({
  items,
  activeId,
  onMarkerClick,
  defaultZoom = 10,
  className,
}: PropertyMapProps) => {
  if (!GOOGLE_MAPS_API_KEY) {
    return (
      <div
        className={cn(
          "flex h-full w-full items-center justify-center rounded-2xl bg-neutral-100 p-6 text-center text-sm text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400",
          className,
        )}
      >
        Map unavailable — Google Maps API key is not configured.
      </div>
    );
  }

  const withCoords = items.filter((item) => item.map);
  const center = withCoords[0]?.map ?? US_CENTER;

  return (
    <div className={cn("h-full w-full overflow-hidden rounded-2xl", className)}>
      <GoogleMapReact
        bootstrapURLKeys={{ key: GOOGLE_MAPS_API_KEY }}
        defaultCenter={US_CENTER}
        center={center}
        defaultZoom={defaultZoom}
        yesIWantToUseGoogleMapApiInternals
      >
        {withCoords.map((item) => (
          <PriceMarker
            key={item.id}
            lat={item.map!.lat}
            lng={item.map!.lng}
            label={item.priceLabel ?? "View"}
            active={item.id === activeId}
            onClick={() => onMarkerClick?.(item.id)}
          />
        ))}
      </GoogleMapReact>
    </div>
  );
};
