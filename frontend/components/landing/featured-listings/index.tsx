import Image from "next/image";
import Link from "next/link";
import { MapPin } from "lucide-react";

import type { FeaturedListing } from "@constants";
import { FEATURED_LISTINGS } from "@constants";
import { Badge } from "@components/ui/voyager/badge";
import { ButtonSecondary } from "@components/ui/voyager/button-secondary";
import { Heading2 } from "@components/ui/voyager/heading2";

import { STYLES } from "./styles";

const ListingCard = ({ listing }: { listing: FeaturedListing }) => (
  <Link href={`/listings/${listing.id}`} className={STYLES.card}>
    <div className={STYLES.imageWrap}>
      <Image
        src={listing.imageSrc}
        alt={listing.imageAlt}
        fill
        className={STYLES.image}
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      />
      <Badge
        name={listing.transactionType}
        color={listing.transactionType === "Sale" ? "green" : "blue"}
        className="absolute top-3 left-3"
      />
    </div>
    <div className={STYLES.body}>
      <span className={STYLES.meta}>{listing.category}</span>
      <h3 className={STYLES.title}>
        <span className="line-clamp-1">{listing.title}</span>
      </h3>
      <div className={STYLES.location}>
        <MapPin className="h-4 w-4 shrink-0" aria-hidden />
        <span className="line-clamp-1">{listing.location}</span>
      </div>
      <div className={STYLES.divider} />
      <div className={STYLES.footer}>
        <span className={STYLES.sqft}>{listing.sqftLabel}</span>
        <span className={STYLES.price}>{listing.priceLabel ?? "—"}</span>
      </div>
    </div>
  </Link>
);

export const FeaturedListings = () => (
  <section className={STYLES.section} aria-labelledby="featured-listings-heading">
    <div className={STYLES.inner}>
      <Heading2
        heading={<span id="featured-listings-heading">Featured listings</span>}
        subHeading={
          <span className="mt-3 block text-neutral-500 dark:text-neutral-400">
            Curated commercial properties across categories and markets.
          </span>
        }
      />
      <div className={STYLES.grid}>
        {FEATURED_LISTINGS.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>

      <div className={STYLES.browseRow}>
        <ButtonSecondary href="/listings">Browse all properties</ButtonSecondary>
      </div>
    </div>
  </section>
);
