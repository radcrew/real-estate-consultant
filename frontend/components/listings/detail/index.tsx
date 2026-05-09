"use client";

import { ListingBackLink } from "./link";
import { ListingMainSection } from "./main";
import { ListingOverviewCard } from "./overview";
import { ListingPhotoCarousel } from "./photo";
import { MOCK_LISTING_DETAIL, type MockListingDetail } from "./mock-data";
import { listingTitle } from "@utils/listings";

type ListingDetailViewProps = {
  data?: MockListingDetail;
};

export const ListingDetailView = ({ data = MOCK_LISTING_DETAIL }: ListingDetailViewProps) => {
  const { property, images } = data;
  const gallery = images.length > 0 ? images : property.image ? [property.image] : [];

  return (
    <div className="min-h-[60vh] bg-muted/20">
      <div className="mx-auto max-w-screen-xl px-4 py-6 sm:py-10">
        <ListingBackLink />

        <ListingPhotoCarousel gallery={gallery} imageTitle={listingTitle(property)} />

        <div className="mt-8 lg:grid lg:grid-cols-[1fr_22rem] lg:items-start lg:gap-10 xl:gap-12">
          <ListingMainSection property={property} />
          <ListingOverviewCard property={property} />
        </div>
      </div>
    </div>
  );
};
