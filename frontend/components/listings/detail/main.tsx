import { ExternalLink, MapPin } from "lucide-react";

import type { ListingProperty } from "@services/listings";
import { listingLocationLine, listingTitle } from "@utils/listings/headline";
import { mapsHref } from "@utils/listings/maps";

type ListingMainSectionProps = {
  property: ListingProperty;
};

export const ListingMainSection = ({ property: p }: ListingMainSectionProps) => {
  const title = listingTitle(p);
  const locationLine = listingLocationLine(p);
  const mapsUrl = mapsHref(p.latitude, p.longitude);

  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-2">
        {p.property_type ? (
          <span className="rounded-md bg-muted px-2.5 py-1 text-xs font-semibold text-foreground">
            {p.property_type}
          </span>
        ) : null}
        {p.listing_type ? (
          <span className="rounded-md bg-primary px-2.5 py-1 text-xs font-semibold text-primary-foreground">
            {p.listing_type}
          </span>
        ) : null}
      </div>

      <h1 className="mt-3 text-balance text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{title}</h1>

      {locationLine ? (
        <p className="mt-2 flex items-start gap-2 text-muted-foreground">
          <MapPin className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
          <span>{locationLine}</span>
        </p>
      ) : null}

      {mapsUrl ? (
        <p className="mt-3">
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary underline-offset-4 hover:underline"
          >
            Open in Google Maps
            <ExternalLink className="size-3.5" aria-hidden />
          </a>
        </p>
      ) : null}

      {p.description ? (
        <section className="mt-8 border-t border-border pt-8" aria-labelledby="listing-description">
          <h2
            id="listing-description"
            className="text-sm font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Description
          </h2>
          <p className="mt-3 max-w-3xl text-pretty text-base leading-relaxed text-foreground">{p.description}</p>
        </section>
      ) : null}
    </div>
  );
};
