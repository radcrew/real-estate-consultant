type ListingDetailNoticeProps = {
  message: string;
  tone?: "neutral" | "error";
};

export const ListingDetailNotice = ({ message, tone = "neutral" }: ListingDetailNoticeProps) => {
  if (tone === "error") {
    return (
      <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
        {message}
      </div>
    );
  }

  return <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">{message}</div>;
};

export const ListingDetailSkeleton = () => (
  <div className="space-y-8">
    <div className="h-[24rem] animate-pulse rounded-xl border border-border bg-muted/70" />
    <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1fr_22rem]">
      <div className="space-y-3">
        <div className="h-6 w-3/4 animate-pulse rounded bg-muted" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
        <div className="h-24 w-full animate-pulse rounded bg-muted" />
      </div>
      <div className="h-56 animate-pulse rounded-xl border border-border bg-muted/70" />
    </div>
  </div>
);
