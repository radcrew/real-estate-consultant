"use client";

import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@contexts/auth";
import { outreachService, type OutreachDraft } from "@services/outreach";
import { getApiErrorMessage } from "@utils/common";

type UseOutreachDraftArgs = {
  propertyId: string | null;
  enabled: boolean;
};

type UseOutreachDraftResult = {
  draft: OutreachDraft | null;
  draftText: string;
  setDraftText: (value: string) => void;
  loadingLatest: boolean;
  saving: boolean;
  generating: boolean;
  error: string | null;
  clearError: () => void;
  refreshLatest: () => Promise<void>;
  generateDraft: () => Promise<OutreachDraft>;
  saveDraft: () => Promise<OutreachDraft>;
};

const emailFromRow = (row: OutreachDraft | null) => row?.draft_email ?? "";

export const useOutreachDraft = ({
  propertyId,
  enabled,
}: UseOutreachDraftArgs): UseOutreachDraftResult => {
  const { session, ready } = useAuth();
  const authenticated = Boolean(ready && session?.accessToken);

  const [draft, setDraft] = useState<OutreachDraft | null>(null);
  const [draftText, setDraftText] = useState("");
  const [loadingLatest, setLoadingLatest] = useState(false);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshLatest = useCallback(async () => {
    const id = propertyId?.trim();
    if (!id || !authenticated) {
      setDraft(null);
      setDraftText("");
      return;
    }
    setLoadingLatest(true);
    setError(null);
    try {
      const row = await outreachService.getLatestDraft(id);
      setDraft(row);
      setDraftText(emailFromRow(row));
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
      setDraft(null);
      setDraftText("");
    } finally {
      setLoadingLatest(false);
    }
  }, [propertyId, authenticated]);

  useEffect(() => {
    if (!enabled || !authenticated) {
      setDraft(null);
      setDraftText("");
      setLoadingLatest(false);
      return;
    }
    const id = propertyId?.trim();
    if (!id) {
      setDraft(null);
      setDraftText("");
      return;
    }

    const controller = new AbortController();
    setLoadingLatest(true);
    setError(null);

    outreachService
      .getLatestDraft(id, { signal: controller.signal })
      .then((row) => {
        if (!controller.signal.aborted) {
          setDraft(row);
          setDraftText(emailFromRow(row));
        }
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(getApiErrorMessage(err));
          setDraft(null);
          setDraftText("");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoadingLatest(false);
        }
      });

    return () => controller.abort();
  }, [propertyId, authenticated, enabled]);

  const generateDraft = useCallback(async () => {
    const id = propertyId?.trim();
    if (!id || !authenticated) {
      throw new Error("Not ready to generate draft.");
    }
    setGenerating(true);
    setError(null);
    try {
      const row = await outreachService.createDraft(id);
      setDraft(row);
      setDraftText(emailFromRow(row));
      return row;
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
      throw err;
    } finally {
      setGenerating(false);
    }
  }, [propertyId, authenticated]);

  const saveDraft = useCallback(async () => {
    const id = draft?.id;
    if (!id) {
      throw new Error("No draft to save.");
    }
    setSaving(true);
    setError(null);
    try {
      const row = await outreachService.patchDraft(id, { draft_email: draftText });
      setDraft(row);
      setDraftText(emailFromRow(row));
      return row;
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
      throw err;
    } finally {
      setSaving(false);
    }
  }, [draft?.id, draftText]);

  return {
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
  };
};
