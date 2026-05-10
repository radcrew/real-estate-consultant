import Image from "next/image";
import Link from "next/link";
import { Search } from "lucide-react";

import type { FeaturedListing } from "@constants";
import { FEATURED_LISTINGS } from "@constants";
import { buttonVariants } from "@components/ui/buttons";
import { cn } from "@utils/common";

import { STYLES } from "./styles";

const ListingCard = ({ listing }: { listing: FeaturedListing }) => (
  <Link
    href={`/listings/${listing.id}`}
    className={STYLES.cardLink}
  >
    <div className={STYLES.cardImageWrap}>
      <Image
        src={listing.imageSrc}
        alt={listing.imageAlt}
        fill
        className={STYLES.cardImage}
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      />
      <div className={STYLES.badgeLeftWrap}>
        <span className={STYLES.badgeLeft}>
          {listing.category}
        </span>
      </div>
      <div className={STYLES.badgeRightWrap}>
        <span className={STYLES.badgeRight}>
          {listing.transactionType}
        </span>
      </div>
    </div>
    <div className={STYLES.cardBody}>
      <h3 className={STYLES.cardTitle}>
        {listing.title}
      </h3>
      <p className={STYLES.cardLocation}>{listing.location}</p>
      <div className={STYLES.cardFooter}>
        <span className={STYLES.cardSqft}>
          {listing.sqftLabel}
        </span>
        {listing.priceLabel ? (
          <span className={STYLES.cardPrice}>
            {listing.priceLabel}
          </span>
        ) : (
          <span className={STYLES.cardPriceEmpty}>—</span>
        )}
      </div>
    </div>
  </Link>
);

export const FeaturedListings = () => (
  <section className={STYLES.section} aria-labelledby="featured-listings-heading">
    <div className={STYLES.inner}>
      <h2 id="featured-listings-heading" className={STYLES.title}>
        Featured Listings
      </h2>
      <div className={STYLES.grid}>
        {FEATURED_LISTINGS.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>

      <div className={STYLES.browseRow}>
        <Link
          href="/listings"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            STYLES.browseButton,
          )}
        >
          <Search className="size-5 shrink-0" aria-hidden />
          Browse All Properties
        </Link>
      </div>
    </div>
  </section>
);
