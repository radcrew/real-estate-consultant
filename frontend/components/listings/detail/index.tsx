"use client";

import { HistoryBackButton } from "@components/ui/buttons/back";
import { listingTitle } from "@utils/listings/headline";

import { useListingDetail } from "../../../hooks/use-listing-detail";
import { ListingMainSection } from "./main";
import { ListingOverviewCard } from "./overview";
import { ListingOutreachSection } from "./outreach";
import { ListingPhotoCarousel } from "./photo";
import { ListingDetailNotice, ListingDetailSkeleton } from "./status";

export const ListingDetailView = () => {
  const { data, loading, error } = useListingDetail();

  const { property, images } = data ?? { property: null, images: [] as string[] };
  const hasData = property !== null;
  const gallery = hasData ? (images.length > 0 ? images : property.image ? [property.image] : []) : [];

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-6 sm:py-10">
        <HistoryBackButton />

        {loading ? (
          <ListingDetailSkeleton />
        ) : error ? (
          <ListingDetailNotice message={error} tone="error" />
        ) : !hasData ? (
          <ListingDetailNotice message="Listing not found." />
        ) : (
          <>
            <ListingPhotoCarousel gallery={gallery} imageTitle={listingTitle(property)} />

            <div className="mt-8 lg:grid lg:grid-cols-[1fr_22rem] lg:items-start lg:gap-10 xl:gap-12">
              <ListingMainSection property={property} />
              <ListingOverviewCard property={property} />
            </div>
            <ListingOutreachSection property={property} />
          </>
        )}
      </div>
    </div>
  );
};
