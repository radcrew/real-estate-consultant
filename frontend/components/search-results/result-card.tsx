import Image from "next/image";
import Link from "next/link";

import { featuredListingsStyles } from "./featured-styles";
import type { RankedPropertyListing } from "./mock-data";

type ResultCardProps = {
  listing: RankedPropertyListing;
};

export const ResultCard = ({ listing }: ResultCardProps) => {
  const s = featuredListingsStyles;

  return (
    <Link href={`/listings/${listing.id}`} className={s.cardLink}>
      <div className={s.cardImageWrap}>
        <Image
          src={listing.imageSrc}
          alt={listing.imageAlt}
          fill
          className={s.cardImage}
          sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        />
        <div className={s.badgeLeftWrap}>
          <span className={s.badgeLeft}>{listing.category}</span>
        </div>
        <div className={s.badgeRightWrap}>
          <span className={s.badgeRight}>{listing.transactionType}</span>
        </div>
        <div className="absolute bottom-2 left-2 sm:bottom-3 sm:left-3">
          <span className="rounded-md bg-amber-600 px-2 py-1 text-xs font-bold tabular-nums text-white shadow-sm">
            {listing.matchScore} match
          </span>
        </div>
      </div>
      <div className={s.cardBody}>
        <h3 className={s.cardTitle}>{listing.title}</h3>
        <p className={s.cardLocation}>{listing.location}</p>
        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
          {listing.matchBlurb}
        </p>
        <div className={s.cardFooter}>
          <span className={s.cardSqft}>{listing.sqftLabel}</span>
          {listing.priceLabel ? (
            <span className={s.cardPrice}>{listing.priceLabel}</span>
          ) : (
            <span className={s.cardPriceEmpty}>—</span>
          )}
        </div>
      </div>
    </Link>
  );
};
