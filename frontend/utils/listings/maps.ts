export const mapsHref = (lat: number | null, lng: number | null): string | null => {
  if (lat == null || lng == null) {
    return null;
  }
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
};
