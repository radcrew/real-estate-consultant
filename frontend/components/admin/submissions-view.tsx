"use client";

import { useEffect, useState } from "react";

import { NoticeCard } from "@components/ui/notice-card";
import { Badge } from "@components/ui/voyager/badge";
import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { ButtonThird } from "@components/ui/voyager/button-third";
import {
  listingsService,
  type ListingSubmissionItem,
  type ListingSubmissionStatus,
} from "@services/listings";
import { getApiErrorMessage } from "@utils/common";

const STATUS_COLOR: Record<ListingSubmissionStatus, "yellow" | "green" | "red"> = {
  pending: "yellow",
  approved: "green",
  rejected: "red",
};

export const AdminSubmissionsView = () => {
  const [items, setItems] = useState<ListingSubmissionItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    void (async () => {
      try {
        const data = await listingsService.listSubmissions({ signal: ac.signal });
        if (!ac.signal.aborted) setItems(data);
      } catch (e) {
        if (!ac.signal.aborted) setError(getApiErrorMessage(e));
      }
    })();
    return () => ac.abort();
  }, []);

  const setStatus = async (id: string, status: ListingSubmissionStatus) => {
    setBusyId(id);
    try {
      const updated = await listingsService.updateSubmission(id, status);
      setItems((prev) =>
        (prev ?? []).map((it) => (it.id === id ? updated : it)),
      );
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setBusyId(null);
    }
  };

  const loading = items === null && !error;

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
        Listing submissions
      </h1>
      <p className="mt-3 text-neutral-500 dark:text-neutral-400">
        Review properties submitted via “List your property”.
      </p>

      {error ? (
        <div className="mt-10 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      {loading ? (
        <p className="mt-10 text-neutral-500 dark:text-neutral-400">Loading…</p>
      ) : null}

      {items && items.length === 0 ? (
        <NoticeCard className="mt-10 text-neutral-600 dark:text-neutral-300">
          No submissions yet.
        </NoticeCard>
      ) : null}

      {items && items.length > 0 ? (
        <div className="mt-10 space-y-4">
          {items.map((it) => (
            <div
              key={it.id}
              className="flex flex-col gap-4 rounded-2xl border border-neutral-200 p-5 sm:flex-row sm:items-center sm:justify-between dark:border-neutral-700"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <Badge name={it.status} color={STATUS_COLOR[it.status]} />
                  {it.property_type ? (
                    <span className="text-xs text-neutral-500 dark:text-neutral-400">
                      {it.property_type} · {it.listing_type}
                    </span>
                  ) : null}
                </div>
                <h2 className="mt-2 truncate font-semibold text-neutral-900 dark:text-neutral-100">
                  {it.title || "Untitled listing"}
                </h2>
                <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                  {[it.city, it.state].filter(Boolean).join(", ")}
                  {it.contact_email ? ` · ${it.contact_email}` : ""}
                </p>
              </div>
              <div className="flex shrink-0 gap-2">
                <ButtonThird
                  sizeClass="px-4 py-2"
                  fontSize="text-sm font-medium"
                  disabled={busyId === it.id || it.status === "rejected"}
                  onClick={() => setStatus(it.id, "rejected")}
                >
                  Reject
                </ButtonThird>
                <ButtonPrimary
                  sizeClass="px-4 py-2"
                  fontSize="text-sm font-medium"
                  disabled={busyId === it.id || it.status === "approved"}
                  onClick={() => setStatus(it.id, "approved")}
                >
                  Approve
                </ButtonPrimary>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
};
