"use client";

import Link from "next/link";
import { Loader2, Mail } from "lucide-react";

import { Button, buttonVariants } from "@components/ui/buttons";
import { useAuth } from "@contexts/auth";
import { useOutreachDraft } from "@hooks/use-outreach-draft";
import type { ListingProperty } from "@services/listings";
import { cn } from "@utils/common";

type ListingOutreachSectionProps = {
  property: ListingProperty;
};

export const ListingOutreachSection = ({ property }: ListingOutreachSectionProps) => {
  const { session, ready } = useAuth();
  const propertyId = typeof property.id === "string" ? property.id.trim() : "";

  const {
    draft,
    draftText,
    setDraftText,
    loadingLatest,
    saving,
    generating,
    error,
    clearError,
    refreshLatest,
    generateDraft,
    saveDraft,
  } = useOutreachDraft({
    propertyId: propertyId || null,
    enabled: Boolean(propertyId),
  });

  if (!propertyId || !ready || !session) {
    return null;
  }

  const brokerLine = [property.listing_broker_name, property.listing_broker_email]
    .filter((v): v is string => typeof v === "string" && v.trim().length > 0)
    .join(" · ");

  const hasDraftText = draftText !== (draft?.draft_email ?? "");
  const canSave = Boolean(draft?.id) && hasDraftText && !saving && !generating && !loadingLatest;

  const onGenerate = async () => {
    clearError();
    try {
      await generateDraft();
    } catch {
    }
  };

  const onSave = async () => {
    if (!draft?.id) return;
    clearError();
    try {
      await saveDraft();
    } catch {
    }
  };

  return (
    <section
      className="mt-10 rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6"
      aria-labelledby="listing-outreach-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h2
            id="listing-outreach-heading"
            className="text-sm font-semibold uppercase tracking-wide text-muted-foreground"
          >
            Broker outreach
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Please review before you send from your own email.
          </p>
          {brokerLine ? (
            <p className="mt-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground/80">Listing contact:</span> {brokerLine}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={generating || loadingLatest}
            onClick={() => void onGenerate()}
          >
            {generating ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Generating…
              </>
            ) : (
              "Generate draft"
            )}
          </Button>
          <Button type="button" variant="default" size="sm" disabled={!canSave} onClick={() => void onSave()}>
            {saving ? (
              <>
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Saving…
              </>
            ) : (
              "Save changes"
            )}
          </Button>
        </div>
      </div>

      {loadingLatest && !draft && !generating ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Loading saved draft…
        </div>
      ) : null}

      {error ? (
        <div
          className="mt-4 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive"
          role="alert"
        >
          <p>{error}</p>
          <Button type="button" variant="ghost" size="xs" className="mt-2 h-auto px-0" onClick={() => void refreshLatest()}>
            Retry load
          </Button>
        </div>
      ) : null}

      <div className="mt-4">
        <label htmlFor="outreach-draft-email" className="sr-only">
          Draft email
        </label>
        <textarea
          id="outreach-draft-email"
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          rows={12}
          disabled={generating || (loadingLatest && !draft)}
          placeholder={
            draft || generating ? "Draft appears here — edit freely, then save." : "Generate a draft to get started."
          }
          className="min-h-[12rem] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed text-foreground shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-60"
        />
      </div>
    </section>
  );
};
