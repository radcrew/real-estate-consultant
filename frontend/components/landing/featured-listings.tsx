import Image from "next/image";
import Link from "next/link";
import { Search } from "lucide-react";

import type { FeaturedListing } from "@constants";
import { FEATURED_LISTINGS } from "@constants";
import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";
const SECTION =
  "border-b border-border/60 bg-muted/30 px-4 py-14 sm:py-16";

const INNER = "mx-auto max-w-screen-xl";

const TITLE =
  "text-center text-2xl font-bold tracking-tight text-foreground sm:text-3xl";

const GRID =
  "mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-7 lg:grid-cols-3 lg:gap-8";

const BROWSE_ROW = "mt-10 flex justify-center sm:mt-12";

const BROWSE_BUTTON =
  "inline-flex items-center gap-2 px-6 font-semibold shadow-none";

const ListingCard = ({ listing }: { listing: FeaturedListing }) => (
  <Link
    href={`/listings/${listing.id}`}
    className="group block overflow-hidden rounded-lg border border-border bg-card shadow-sm transition-shadow hover:shadow-md"
  >
    <div className="relative aspect-[16/10] bg-muted">
      <Image
        src={listing.imageSrc}
        alt={listing.imageAlt}
        fill
        className="object-cover transition-transform duration-300 group-hover:scale-[1.02]"
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
      />
      <div className="absolute left-2 top-2 sm:left-3 sm:top-3">
        <span className="rounded-md bg-background px-2 py-0.5 text-xs font-semibold text-foreground shadow-sm">
          {listing.category}
        </span>
      </div>
      <div className="absolute right-2 top-2 sm:right-3 sm:top-3">
        <span className="rounded-md bg-primary px-2 py-0.5 text-xs font-semibold text-primary-foreground shadow-sm">
          {listing.transactionType}
        </span>
      </div>
    </div>
    <div className="p-4 sm:p-5">
      <h3 className="line-clamp-2 text-base font-bold leading-snug text-foreground sm:text-lg">
        {listing.title}
      </h3>
      <p className="mt-1.5 text-sm text-muted-foreground">{listing.location}</p>
      <div className="mt-4 flex items-end justify-between gap-3 border-t border-border/60 pt-4">
        <span className="text-sm font-bold tabular-nums text-foreground">
          {listing.sqftLabel}
        </span>
        {listing.priceLabel ? (
          <span className="shrink-0 text-xs font-medium text-muted-foreground">
            {listing.priceLabel}
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">—</span>
        )}
      </div>
    </div>
  </Link>
);

export const FeaturedListings = () => (
  <section className={SECTION} aria-labelledby="featured-listings-heading">
    <div className={INNER}>
      <h2 id="featured-listings-heading" className={TITLE}>
        Featured Listings
      </h2>
      <div className={GRID}>
        {FEATURED_LISTINGS.map((listing) => (
          <ListingCard key={listing.id} listing={listing} />
        ))}
      </div>

      <div className={BROWSE_ROW}>
        <Link
          href="/listings"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            BROWSE_BUTTON
          )}
        >
          <Search className="size-5 shrink-0" aria-hidden />
          Browse All Properties
        </Link>
      </div>
    </div>
  </section>
)
