import type { MockListingProperty } from "./mock-data";
import { formatFt, formatSqft, formatUsd } from "./utils/format";

const overviewBorderedRow = "flex flex-col gap-0.5 border-b border-border/70 pb-4 last:border-0 last:pb-0";
const overviewLabel = "text-xs font-medium text-muted-foreground";
const overviewGrid = "grid grid-cols-2 gap-4 border-t border-border/70 pt-4";
const overviewValueCompact = "mt-0.5 text-sm font-semibold tabular-nums";

type ListingOverviewCardProps = {
  property: MockListingProperty;
};

const InfoItem = ({ label, value }: { label: string; value: string }) => {
  return (
    <div className={overviewBorderedRow}>
      <dt className={overviewLabel}>{label}</dt>
      <dd className={overviewValueCompact}>{value}</dd>
    </div>
  );
};

export const ListingOverviewCard = ({ property: p }: ListingOverviewCardProps) => {
  const priceLabel = formatUsd(p.price);
  const rentLabel = formatUsd(p.rent);
  const sqftLabel = formatSqft(p.size_sqft);
  const heightLabel = formatFt(p.clear_height);

  return (
    <aside className="mt-10 lg:mt-0">
      <div className="sticky top-6 rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Overview</h2>
        <dl className="mt-4 space-y-4">
          <InfoItem label="Price" value={priceLabel ?? "—"} />
          <InfoItem label="Rent (est.)" value={rentLabel ?? "—"} />
          <InfoItem label="Size" value={sqftLabel ?? "—"} />
          {(heightLabel || p.loading_docks != null) && (
            <div className={overviewGrid}>
              {heightLabel ? (
                <div>
                  <dt className={overviewLabel}>Clear height</dt>
                  <dd className={overviewValueCompact}>{heightLabel}</dd>
                </div>
              ) : null}
              {p.loading_docks != null ? (
                <div>
                  <dt className={overviewLabel}>Loading docks</dt>
                  <dd className={overviewValueCompact}>{p.loading_docks}</dd>
                </div>
              ) : null}
            </div>
          )}
        </dl>
      </div>
    </aside>
  );
};
