import { cn } from "@lib/utils";

type SearchFilterSkeletonProps = {
  className?: string;
};

/** Placeholder bar matching ``SearchFilter`` layout while results load. */
export const SearchFilterSkeleton = ({ className }: SearchFilterSkeletonProps) => (
  <section
    className={cn(
      "flex flex-nowrap items-center gap-2 overflow-hidden py-2",
      className,
    )}
    aria-busy="true"
    aria-label="Loading search filters"
  >
    <div className="flex min-w-0 flex-1 flex-nowrap items-center gap-2 overflow-x-hidden">
      <div className="h-9 w-52 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-28 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-32 shrink-0 animate-pulse rounded-md bg-muted" />
    </div>
    <div className="ml-auto flex shrink-0 gap-2">
      <div className="h-9 w-14 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="h-9 w-20 shrink-0 animate-pulse rounded-md bg-muted" />
    </div>
  </section>
);
