import type { MockListingProperty } from "./mock-data";
import { formatFt, formatSqft, formatUsd } from "./utils/format";

type ListingOverviewCardProps = {
  property: MockListingProperty;
};

export const ListingOverviewCard = ({ property: p }: ListingOverviewCardProps) => {
  const priceLabel = formatUsd(p.price);
  const rentLabel = formatUsd(p.rent);
  const sqftLabel = formatSqft(p.size_sqft);
  const clearLabel = formatFt(p.clear_height);

  return (
    <aside className="mt-10 lg:mt-0">
      <div className="sticky top-6 rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Overview</h2>
        <dl className="mt-4 space-y-4">
          <div className="flex flex-col gap-0.5 border-b border-border/70 pb-4 last:border-0 last:pb-0">
            <dt className="text-xs font-medium text-muted-foreground">Price</dt>
            <dd className="text-xl font-bold tabular-nums text-foreground">{priceLabel ?? "—"}</dd>
          </div>
          <div className="flex flex-col gap-0.5 border-b border-border/70 pb-4 last:border-0 last:pb-0">
            <dt className="text-xs font-medium text-muted-foreground">Rent (est.)</dt>
            <dd className="text-lg font-semibold tabular-nums text-foreground">{rentLabel ?? "—"}</dd>
          </div>
          <div className="flex flex-col gap-0.5 border-b border-border/70 pb-4 last:border-0 last:pb-0">
            <dt className="text-xs font-medium text-muted-foreground">Size</dt>
            <dd className="text-lg font-semibold tabular-nums text-foreground">{sqftLabel ?? "—"}</dd>
          </div>
          {(clearLabel || p.loading_docks != null) && (
            <div className="grid grid-cols-2 gap-4 border-t border-border/70 pt-4">
              {clearLabel ? (
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Clear height</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular-nums">{clearLabel}</dd>
                </div>
              ) : null}
              {p.loading_docks != null ? (
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Loading docks</dt>
                  <dd className="mt-0.5 text-sm font-semibold tabular-nums">{p.loading_docks}</dd>
                </div>
              ) : null}
            </div>
          )}
        </dl>
      </div>
    </aside>
  );
};
