import Image from "next/image";
import Link from "next/link";
import { Search } from "lucide-react";

import type { FeaturedListing } from "@constants";
import { FEATURED_LISTINGS } from "@constants";
import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";

import { styles } from "./styles";

const ListingCard = ({ listing }: { listing: FeaturedListing }) => (
  <Link
    href={`/listings/${listing.id}`}
    className={styles.cardLink}
  >
    <div className={styles.cardImageWrap}>
      <Image
        src={listing.imageSrc}
        alt={listing.imageAlt}
        fill
        className={styles.cardImage}
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      />
      <div className={styles.badgeLeftWrap}>
        <span className={styles.badgeLeft}>
          {listing.category}
        </span>
      </div>
      <div className={styles.badgeRightWrap}>
        <span className={styles.badgeRight}>
          {listing.transactionType}
        </span>
      </div>
    </div>
    <div className={styles.cardBody}>
      <h3 className={styles.cardTitle}>
        {listing.title}
      </h3>
      <p className={styles.cardLocation}>{listing.location}</p>
      <div className={styles.cardFooter}>
        <span className={styles.cardSqft}>
          {listing.sqftLabel}
        </span>
        {listing.priceLabel ? (
          <span className={styles.cardPrice}>
            {listing.priceLabel}
          </span>
        ) : (
          <span className={styles.cardPriceEmpty}>—</span>
        )}
      </div>
    </div>
  </Link>
);

export const FeaturedListings = () => (
  <section className={styles.section} aria-labelledby="featured-listings-heading">
    <div className={styles.inner}>
      <h2 id="featured-listings-heading" className={styles.title}>
        Featured Listings
      </h2>
      <div className={styles.grid}>
        {FEATURED_LISTINGS.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>

      <div className={styles.browseRow}>
        <Link
          href="/listings"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            styles.browseButton,
          )}
        >
          <Search className="size-5 shrink-0" aria-hidden />
          Browse All Properties
        </Link>
      </div>
    </div>
  </section>
);
