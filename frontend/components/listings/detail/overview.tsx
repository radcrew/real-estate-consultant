import { formatFeet, formatMoneyOrNull, formatSqft } from "@utils/common";

import type { ListingProperty } from "@services/listings";
import { STYLES } from "./styles";

type ListingOverviewCardProps = {
  property: ListingProperty;
};

const InfoItem = ({ label, value }: { label: string; value: string }) => {
  return (
    <div className={STYLES.overviewBorderedRow}>
      <dt className={STYLES.overviewLabel}>{label}</dt>
      <dd className={STYLES.overviewValueCompact}>{value}</dd>
    </div>
  );
};

export const ListingOverviewCard = ({ property: p }: ListingOverviewCardProps) => {
  const priceLabel = formatMoneyOrNull(p.price);
  const rentLabel = formatMoneyOrNull(p.rent);
  const sqftLabel = formatSqft(p.size_sqft);
  const heightLabel = formatFeet(p.clear_height);

  return (
    <aside className="mt-10 lg:mt-0">
      <div className="sticky top-6 rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Overview</h2>
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
                  <dd className={STYLES.overviewValueCompact}>{p.loading_docks}</dd>
                </div>
              ) : null}
            </div>
          )}
        </dl>
      </div>
    </aside>
  );
};
