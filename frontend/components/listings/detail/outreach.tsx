"use client";

import { Loader2 } from "lucide-react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { ButtonThird } from "@components/ui/button-third";
import { Textarea } from "@components/ui/textarea";
import { useAuth } from "@contexts/auth";
import { useOutreachDraft } from "@hooks/use-outreach-draft";
import type { ListingProperty } from "@services/listings";

type ListingOutreachSectionProps = {
  property: ListingProperty;
};

export const ListingOutreachSection = ({
  property,
}: ListingOutreachSectionProps) => {
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
  const canSave =
    Boolean(draft?.id) && hasDraftText && !saving && !generating && !loadingLatest;

  const onGenerate = async () => {
    clearError();
    try {
      await generateDraft();
    } catch {}
  };

  const onSave = async () => {
    if (!draft?.id) return;
    clearError();
    try {
      await saveDraft();
    } catch {}
  };

  return (
    <section
      className="mt-10 rounded-2xl border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-900"
      aria-labelledby="listing-outreach-heading"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <h2
            id="listing-outreach-heading"
            className="text-sm font-semibold tracking-wide text-neutral-500 uppercase dark:text-neutral-400"
          >
            Broker outreach
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-neutral-500 dark:text-neutral-400">
            Please review before you send from your own email.
          </p>
          {brokerLine ? (
            <p className="mt-2 text-xs text-neutral-500 dark:text-neutral-400">
              <span className="font-medium text-neutral-700 dark:text-neutral-200">
                Listing contact:
              </span>{" "}
              {brokerLine}
            </p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <ButtonThird
            type="button"
            disabled={generating || loadingLatest}
            loading={generating}
            onClick={onGenerate}
            sizeClass="px-4 py-2"
            fontSize="text-sm font-medium"
          >
            {generating ? "Generating…" : "Generate draft"}
          </ButtonThird>
          <ButtonPrimary
            type="button"
            disabled={!canSave}
            loading={saving}
            onClick={onSave}
            sizeClass="px-4 py-2"
            fontSize="text-sm font-medium"
          >
            {saving ? "Saving…" : "Save changes"}
          </ButtonPrimary>
        </div>
      </div>

      {loadingLatest && !draft && !generating ? (
        <div className="mt-4 flex items-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Loading saved draft…
        </div>
      ) : null}

      {error ? (
        <div
          className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-400"
          role="alert"
        >
          <p>{error}</p>
          <button
            type="button"
            onClick={refreshLatest}
            className="mt-2 text-sm font-medium underline underline-offset-4"
          >
            Retry load
          </button>
        </div>
      ) : null}

      <div className="mt-4">
        <label htmlFor="outreach-draft-email" className="sr-only">
          Draft email
        </label>
        <Textarea
          id="outreach-draft-email"
          value={draftText}
          onChange={(e) => setDraftText(e.target.value)}
          rows={12}
          disabled={generating || (loadingLatest && !draft)}
          placeholder={
            draft || generating
              ? "Draft appears here — edit freely, then save."
              : "Generate a draft to get started."
          }
          className="min-h-[12rem] resize-y leading-relaxed"
        />
      </div>
    </section>
  );
};
