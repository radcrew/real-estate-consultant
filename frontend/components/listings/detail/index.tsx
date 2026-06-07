"use client";

import { HistoryBackButton } from "@components/ui/buttons/back";
import { ButtonThird } from "@components/ui/voyager/button-third";
import { detailToModel } from "@components/voyager/listing-model";
import { PropertyGallery } from "@components/voyager/property-gallery";

import { useListingDetail } from "../../../hooks/use-listing-detail";
import { ListingActions } from "./actions";
import { ListingMainSection } from "./main";
import { ListingOverviewCard } from "./overview";
import { ListingLocationSection } from "./location";
import { ListingOutreachSection } from "./outreach";
import { ListingDetailNotice, ListingDetailSkeleton } from "./status";

export const ListingDetailView = () => {
  const { data, loading, error } = useListingDetail();
  const model = data ? detailToModel(data) : null;
  const property = data?.property ?? null;

  return (
    <div className="min-h-[60vh]">
      <div className="mx-auto max-w-screen-xl px-4 py-8 lg:py-10">
        <HistoryBackButton />

        <div className="mt-6">
          {loading ? (
            <ListingDetailSkeleton />
          ) : error || !property || !model ? (
            <ListingDetailNotice
              title="Listing unavailable"
              message="We couldn't load this listing. It may have been removed, or the link is invalid."
              action={<ButtonThird href="/listings">Back to listings</ButtonThird>}
            />
          ) : (
            <>
              <div className="mb-4 flex justify-end">
                <ListingActions />
              </div>

              <PropertyGallery images={model.galleryImgs} alt={model.title} />

              <div className="mt-10 lg:grid lg:grid-cols-[1fr_22rem] lg:items-start lg:gap-10 xl:gap-12">
                <ListingMainSection property={property} />
                <ListingOverviewCard property={property} />
              </div>

              <ListingLocationSection model={model} />

              <ListingOutreachSection property={property} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
