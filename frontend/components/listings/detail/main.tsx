import { ExternalLink, MapPin } from "lucide-react";

import { Badge } from "@components/ui/voyager/badge";
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
  const txn = p.listing_type?.trim();

  return (
    <div className="min-w-0">
      <div className="flex flex-wrap items-center gap-2">
        {p.property_type ? <Badge name={p.property_type} color="gray" /> : null}
        {txn ? (
          <Badge
            name={txn}
            color={txn.toLowerCase().includes("sale") ? "green" : "blue"}
          />
        ) : null}
      </div>

      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-neutral-900 sm:text-3xl dark:text-neutral-100">
        {title}
      </h1>

      {locationLine ? (
        <p className="mt-2 flex items-start gap-2 text-neutral-500 dark:text-neutral-400">
          <MapPin className="mt-0.5 size-4 shrink-0" aria-hidden />
          <span>{locationLine}</span>
        </p>
      ) : null}

      {mapsUrl ? (
        <p className="mt-3">
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 underline-offset-4 hover:underline"
          >
            Open in Google Maps
            <ExternalLink className="size-3.5" aria-hidden />
          </a>
        </p>
      ) : null}

      {p.description ? (
        <section
          className="mt-8 border-t border-neutral-100 pt-8 dark:border-neutral-800"
          aria-labelledby="listing-description"
        >
          <h2
            id="listing-description"
            className="text-sm font-semibold tracking-wide text-neutral-500 uppercase dark:text-neutral-400"
          >
            Description
          </h2>
          <p className="mt-3 max-w-3xl text-base leading-relaxed text-neutral-700 dark:text-neutral-300">
            {p.description}
          </p>
        </section>
      ) : null}
    </div>
  );
};
