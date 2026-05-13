import Image from "next/image";
import Link from "next/link";

import type { ResultCardListing } from "@utils/search/property";

import { STYLES } from "@components/landing/featured-listings/styles";


type ResultCardProps = {
  listing: ResultCardListing;
};

export const ResultCard = ({ listing }: ResultCardProps) => {
  return (
    <Link href={`/listings/${listing.id}`} className={STYLES.cardLink}>
      <div className={STYLES.cardImageWrap}>
        {listing.imageSrc ? (
          <Image
            src={listing.imageSrc}
            alt={listing.imageAlt}
            fill
            className={STYLES.cardImage}
            sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 bg-muted" aria-hidden />
        )}
        <div className={STYLES.badgeLeftWrap}>
          <span className={STYLES.badgeLeft}>{listing.category}</span>
        </div>
        <div className={STYLES.badgeRightWrap}>
          <span className={STYLES.badgeRight}>{listing.transactionType}</span>
        </div>
        <div className="absolute bottom-2 left-2 sm:bottom-3 sm:left-3">
          <span className="rounded-md bg-amber-600 px-2 py-1 text-xs font-bold tabular-nums text-white shadow-sm">
            {listing.matchScore}% match
          </span>
        </div>
      </div>
      <div className={STYLES.cardBody}>
        <h3 className={STYLES.cardTitle}>{listing.title}</h3>
        <p className={STYLES.cardLocation}>{listing.location}</p>
        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
          {listing.matchBlurb}
        </p>
        <div className={STYLES.cardFooter}>
          <span className={STYLES.cardSqft}>{listing.sqftLabel}</span>
          {listing.priceLabel ? (
            <span className={STYLES.cardPrice}>{listing.priceLabel}</span>
          ) : (
            <span className={STYLES.cardPriceEmpty}>—</span>
          )}
        </div>
      </div>
    </Link>
  );
};
