import Link from "next/link";

import { formatFeet, formatMoneyOrNull, formatSqft } from "@utils/common";

import type { ListingProperty } from "@services/listings";
import { STYLES } from "./styles";

type ListingOverviewCardProps = {
  property: ListingProperty;
};

const InfoItem = ({ label, value }: { label: string; value: string }) => (
  <div className={STYLES.overviewBorderedRow}>
    <dt className={STYLES.overviewLabel}>{label}</dt>
    <dd className={STYLES.overviewValueCompact}>{value}</dd>
  </div>
);

export const ListingOverviewCard = ({ property: p }: ListingOverviewCardProps) => {
  const priceLabel = formatMoneyOrNull(p.price);
  const rentLabel = formatMoneyOrNull(p.rent);
  const sqftLabel = formatSqft(p.size_sqft);
  const heightLabel = formatFeet(p.clear_height);

  return (
    <aside className="mt-10 lg:mt-0">
      <div className="sticky top-24 rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
        <h2 className="text-sm font-semibold tracking-wide text-neutral-500 uppercase dark:text-neutral-400">
          Overview
        </h2>
        <dl className="mt-4 space-y-4">
          <InfoItem label="Price" value={priceLabel ?? "—"} />
          <InfoItem label="Rent (est.)" value={rentLabel ?? "—"} />
          <InfoItem label="Size" value={sqftLabel ?? "—"} />
          {(heightLabel || p.loading_docks != null) && (
            <div className={STYLES.overviewGrid}>
              {heightLabel ? (
                <div>
                  <dt className={STYLES.overviewLabel}>Clear height</dt>
                  <dd className={STYLES.overviewValueCompact}>{heightLabel}</dd>
                </div>
              ) : null}
              {p.loading_docks != null ? (
                <div>
                  <dt className={STYLES.overviewLabel}>Loading docks</dt>
                  <dd className={STYLES.overviewValueCompact}>
                    {p.loading_docks}
                  </dd>
                </div>
              ) : null}
            </div>
          )}
        </dl>
        {p.listing_broker_name ||
        p.listing_broker_email ||
        p.listing_broker_phone ? (
          <div className="mt-4 border-t border-neutral-100 pt-4 dark:border-neutral-800">
            <h3 className={STYLES.overviewLabel}>Listing broker</h3>
            <div className="mt-2 space-y-3">
              {p.listing_broker_name ? (
                <div className={STYLES.overviewBorderedRow}>
                  <div className={STYLES.overviewLabel}>Name</div>
                  <div className={STYLES.overviewValueCompact}>
                    <Link
                      href={`/agents/${encodeURIComponent(p.listing_broker_name)}`}
                      className="text-primary-600 underline-offset-4 hover:underline"
                    >
                      {p.listing_broker_name}
                    </Link>
                  </div>
                </div>
              ) : null}
              {p.listing_broker_email ? (
                <div className={STYLES.overviewBorderedRow}>
                  <div className={STYLES.overviewLabel}>Email</div>
                  <div className={STYLES.overviewValueCompact}>
                    {p.listing_broker_email}
                  </div>
                </div>
              ) : null}
              {p.listing_broker_phone ? (
                <div className={STYLES.overviewBorderedRow}>
                  <div className={STYLES.overviewLabel}>Phone</div>
                  <div className={STYLES.overviewValueCompact}>
                    {p.listing_broker_phone}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>
    </aside>
  );
};
